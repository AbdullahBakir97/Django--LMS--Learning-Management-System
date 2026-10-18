from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.engagement import selectors as engagement

from . import selectors, services
from .models import Event, Group, Membership, Post
from .serializers import (
    EventSerializer,
    GroupMemberSerializer,
    GroupSerializer,
    PostSerializer,
    PostWriteSerializer,
    RoleSerializer,
    RsvpSerializer,
)

User = get_user_model()


def post_context(request, posts) -> dict:
    ids = [p.id for p in posts]
    return {
        "request": request,
        "reactions": engagement.reaction_summary("post", ids, request.user),
        "comment_counts": engagement.comment_counts("post", ids),
    }


def group_for(request, slug) -> Group:
    return get_object_or_404(selectors.groups_visible(request.user), slug=slug)


class GroupViewSet(viewsets.ModelViewSet):
    """Groups. Private groups are listed, but their posts and members are for members only."""

    queryset = Group.objects.none()  # for the schema; get_queryset() scopes to the user

    serializer_class = GroupSerializer
    lookup_field = "slug"
    search_fields = ["name", "description"]
    filterset_fields = ["privacy"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        qs = selectors.groups_visible(self.request.user)
        if self.request.query_params.get("mine") == "true":
            qs = qs.filter(memberships__user=self.request.user)
        return qs

    def perform_create(self, serializer):
        group = services.create_group(self.request.user, **serializer.validated_data)
        serializer.instance = self.get_queryset().get(pk=group.pk)

    def perform_update(self, serializer):
        services.update_group(self.request.user, serializer.instance, **serializer.validated_data)

    def perform_destroy(self, instance):
        services.delete_group(self.request.user, instance)

    @extend_schema(request=None, responses=GroupSerializer)
    @action(detail=True, methods=["post"])
    def join(self, request, slug=None):
        services.join(request.user, self.get_object())
        return Response(self.get_serializer(self.get_queryset().get(slug=slug)).data)

    @extend_schema(request=None, responses=GroupSerializer)
    @action(detail=True, methods=["post"])
    def leave(self, request, slug=None):
        services.leave(request.user, self.get_object())
        return Response(self.get_serializer(self.get_queryset().get(slug=slug)).data)

    @extend_schema(
        responses=GroupMemberSerializer(many=True),
        parameters=[OpenApiParameter("status", OpenApiTypes.STR, enum=["active", "pending"])],
    )
    @action(detail=True, methods=["get"], pagination_class=None)
    def members(self, request, slug=None):
        group = self.get_object()
        wanted = request.query_params.get("status", "active")
        if not selectors.can_see_group_content(request.user, group):
            raise Http404
        if wanted == "pending":
            services._require_manager(request.user, group)
        rows = (
            Membership.objects.filter(group=group, status=wanted)
            .select_related("user__profile")
            .order_by("role", "created_at")
        )
        return Response(GroupMemberSerializer(rows, many=True).data)

    @extend_schema(responses=PostSerializer(many=True))
    @action(detail=True, methods=["get"])
    def posts(self, request, slug=None):
        group = self.get_object()
        if not selectors.can_see_group_content(request.user, group):
            raise Http404
        page = self.paginate_queryset(selectors.posts_in(group))
        return self.get_paginated_response(
            PostSerializer(page, many=True, context=post_context(request, page)).data
        )


class MemberView(APIView):
    """Managers approve (POST .../approve/), remove (DELETE), or the owner sets a role (PATCH)."""

    @extend_schema(request=None, responses=GroupMemberSerializer)
    def post(self, request, slug, user_id):
        m = services.approve(request.user, group_for(request, slug), user_id)
        return Response(GroupMemberSerializer(m).data)

    @extend_schema(request=RoleSerializer, responses=GroupMemberSerializer)
    def patch(self, request, slug, user_id):
        data = RoleSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        m = services.set_role(
            request.user, group_for(request, slug), user_id, data.validated_data["role"]
        )
        return Response(GroupMemberSerializer(m).data)

    @extend_schema(responses={204: None})
    def delete(self, request, slug, user_id):
        services.remove_member(request.user, group_for(request, slug), user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    parameters=[OpenApiParameter("author", OpenApiTypes.STR, description="A username: their posts")]
)
class PostViewSet(viewsets.ModelViewSet):
    """GET /posts/ is your feed; ?author=<username> is someone's posts."""

    queryset = Post.objects.none()  # for the schema; get_queryset() scopes to the user

    serializer_class = PostSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        user = self.request.user
        if self.action == "list":
            author = self.request.query_params.get("author")
            if author:
                return selectors.posts_by(get_object_or_404(User, username=author), user)
            return selectors.feed_for(user)
        return selectors.posts_base().filter(
            Q(group__isnull=True) | Q(group_id__in=selectors.readable_groups(user))
        )

    def get_serializer_context(self):
        return {"request": self.request}

    def list(self, request):
        page = self.paginate_queryset(self.get_queryset())
        return self.get_paginated_response(
            PostSerializer(page, many=True, context=post_context(request, page)).data
        )

    def retrieve(self, request, pk=None):
        post = self.get_object()
        return Response(PostSerializer(post, context=post_context(request, [post])).data)

    @extend_schema(request=PostWriteSerializer, responses={201: PostSerializer})
    def create(self, request):
        data = PostWriteSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        slug = data.validated_data.get("group_slug")
        group = group_for(request, slug) if slug else None
        post = services.create_post(request.user, data.validated_data["body"], group)
        return Response(
            PostSerializer(post, context=post_context(request, [post])).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(request=PostWriteSerializer, responses=PostSerializer)
    def partial_update(self, request, pk=None):
        data = PostWriteSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        post = services.edit_post(request.user, self.get_object(), data.validated_data["body"])
        return Response(PostSerializer(post, context=post_context(request, [post])).data)

    def perform_destroy(self, instance):
        services.delete_post(self.request.user, instance)


@extend_schema(
    parameters=[
        OpenApiParameter("when", OpenApiTypes.STR, enum=["upcoming", "past"]),
        OpenApiParameter("group", OpenApiTypes.STR, description="A group slug"),
        OpenApiParameter("attending", OpenApiTypes.BOOL),
    ]
)
class EventViewSet(viewsets.ModelViewSet):
    """Events you can see: open ones and those in groups you can read."""

    queryset = Event.objects.none()  # for the schema; get_queryset() scopes to the user

    serializer_class = EventSerializer
    http_method_names = ["get", "post", "patch", "delete", "put"]

    def get_queryset(self):
        qs = selectors.events_visible(self.request.user)
        params = self.request.query_params
        if self.action == "list":
            now = timezone.now()
            qs = (
                qs.filter(starts_at__lt=now)
                if params.get("when") == "past"
                else qs.filter(ends_at__gte=now)
            )
            if params.get("group"):
                qs = qs.filter(group__slug=params["group"])
            if params.get("attending") == "true":
                qs = qs.filter(attendances__user=self.request.user)
        return qs

    def paginate_queryset(self, queryset):
        if self.paginator is not None:
            self.paginator.ordering = (
                "-starts_at" if self.request.query_params.get("when") == "past" else "starts_at"
            )
        return super().paginate_queryset(queryset)

    def perform_create(self, serializer):
        data = dict(serializer.validated_data)
        slug = data.pop("group_slug", None)
        group = group_for(self.request, slug) if slug else None
        event = services.create_event(self.request.user, group, **data)
        serializer.instance = self.get_queryset().get(pk=event.pk)

    def perform_update(self, serializer):
        data = dict(serializer.validated_data)
        data.pop("group_slug", None)
        services.update_event(self.request.user, serializer.instance, **data)
        serializer.instance = self.get_queryset().get(pk=serializer.instance.pk)

    def perform_destroy(self, instance):
        services.delete_event(self.request.user, instance)

    @extend_schema(request=RsvpSerializer, responses=EventSerializer, methods=["PUT"])
    @extend_schema(request=None, responses=EventSerializer, methods=["DELETE"])
    @action(detail=True, methods=["put", "delete"])
    def rsvp(self, request, pk=None):
        event = self.get_object()
        if request.method == "DELETE":
            services.cancel_rsvp(request.user, event)
        else:
            data = RsvpSerializer(data=request.data)
            data.is_valid(raise_exception=True)
            services.rsvp(request.user, event, data.validated_data["status"])
        return Response(self.get_serializer(self.get_queryset().get(pk=event.pk)).data)
