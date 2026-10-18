from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from . import selectors, services
from .models import Connection, Follow
from .serializers import (
    ConnectionSerializer,
    ConnectRequestSerializer,
    FollowerSerializer,
    FollowingSerializer,
    RelationshipSerializer,
    SuggestionSerializer,
)


def person(username):
    return get_object_or_404(selectors.people(), username=username)


class RelationshipView(APIView):
    """How you relate to someone: follow both ways, counts, and the connection if any."""

    @extend_schema(responses=RelationshipSerializer)
    def get(self, request, username):
        return Response(selectors.relationship(request.user, person(username)))


class FollowView(APIView):
    @extend_schema(request=None, responses=RelationshipSerializer)
    def post(self, request, username):
        other = person(username)
        services.follow(request.user, other)
        return Response(selectors.relationship(request.user, other), status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=RelationshipSerializer)
    def delete(self, request, username):
        other = person(username)
        services.unfollow(request.user, other)
        return Response(selectors.relationship(request.user, other))


class FollowersView(generics.ListAPIView):
    """People following this user, newest first."""

    serializer_class = FollowerSerializer

    def get_queryset(self):
        return Follow.objects.filter(following=person(self.kwargs["username"])).select_related(
            "follower__profile"
        )


class FollowingView(generics.ListAPIView):
    """People this user follows, newest first."""

    serializer_class = FollowingSerializer

    def get_queryset(self):
        return Follow.objects.filter(follower=person(self.kwargs["username"])).select_related(
            "following__profile"
        )


class SuggestionsView(generics.ListAPIView):
    """People who share your skills and are not linked to you yet."""

    serializer_class = SuggestionSerializer
    pagination_class = None

    def get_queryset(self):
        return selectors.suggestions_for(self.request.user)


@extend_schema(
    parameters=[
        OpenApiParameter(
            "status",
            OpenApiTypes.STR,
            enum=["accepted", "incoming", "outgoing"],
            description="accepted (default), or pending requests by direction",
        )
    ]
)
class ConnectionViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Your connections and requests. Rows you are not part of are 404."""

    serializer_class = ConnectionSerializer
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        user = self.request.user
        if self.action == "list":
            wanted = self.request.query_params.get("status", "accepted")
            if wanted in ("incoming", "outgoing"):
                return selectors.requests_for(user, wanted)
            return selectors.connections_of(user)
        return Connection.objects.filter(Q(requester=user) | Q(addressee=user))

    @extend_schema(request=ConnectRequestSerializer, responses={201: ConnectionSerializer})
    def create(self, request):
        data = ConnectRequestSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        connection = services.request_connection(
            request.user, person(data.validated_data["username"])
        )
        return Response(self.get_serializer(connection).data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        services.remove(self.request.user, instance)

    @extend_schema(request=None, responses=ConnectionSerializer)
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        return Response(self.get_serializer(services.accept(request.user, self.get_object())).data)

    @extend_schema(request=None, responses={204: None})
    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        services.decline(request.user, self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)
