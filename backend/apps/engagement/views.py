from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import CursorPagination

from . import registry, selectors, services
from .models import Comment
from .serializers import (
    CommentSerializer,
    CommentWriteSerializer,
    ReactionSummarySerializer,
    ReactionWriteSerializer,
)


class OldestFirst(CursorPagination):
    ordering = "created_at"


def _context(request, comments, target, obj) -> dict:
    ids = [c.id for c in comments] + [r.id for c in comments for r in c.replies.all()]
    return {
        "request": request,
        "reactions": selectors.reaction_summary("comment", ids, request.user),
        "moderator": services.can_moderate(request.user, target, obj),
    }


class CommentsView(generics.GenericAPIView):
    """The discussion on a target, e.g. /api/engagement/lesson/12/comments/."""

    queryset = Comment.objects.none()  # for the schema; get_queryset() scopes to the user

    pagination_class = OldestFirst
    serializer_class = CommentSerializer

    @extend_schema(responses=CommentSerializer(many=True))
    def get(self, request, key, pk):
        target, obj = registry.resolve(key, pk, request.user)
        page = self.paginate_queryset(selectors.thread(key, obj.pk))
        data = CommentSerializer(page, many=True, context=_context(request, page, target, obj)).data
        return self.get_paginated_response(data)

    @extend_schema(request=CommentWriteSerializer, responses={201: CommentSerializer})
    def post(self, request, key, pk):
        target, obj = registry.resolve(key, pk, request.user)
        data = CommentWriteSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        parent_id = data.validated_data.get("parent")
        parent = Comment.objects.filter(pk=parent_id).first() if parent_id else None
        if parent_id and parent is None:
            raise ValidationError({"parent": "Reply to a comment in this thread."})
        comment = services.add_comment(
            request.user, target, obj, data.validated_data["body"], parent
        )
        context = _context(request, [comment], target, obj)
        return Response(
            CommentSerializer(comment, context=context).data, status=status.HTTP_201_CREATED
        )


class CommentDetailView(APIView):
    """Edit your comment, or remove it (author, the target's owner, or an admin)."""

    def _load(self, request, pk):
        comment = get_object_or_404(Comment.objects.select_related("author__profile"), pk=pk)
        target, obj = registry.resolve(comment.target_type, comment.target_id, request.user)
        if comment.deleted_at is not None:
            raise Http404("Not found.")
        return comment, target, obj

    @extend_schema(request=CommentWriteSerializer, responses=CommentSerializer)
    def patch(self, request, pk):
        comment, target, obj = self._load(request, pk)
        data = CommentWriteSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        comment = services.edit_comment(request.user, comment, data.validated_data["body"])
        context = _context(request, [comment], target, obj)
        return Response(CommentSerializer(comment, context=context).data)

    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        comment, target, obj = self._load(request, pk)
        services.delete_comment(request.user, comment, target, obj)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReactionsView(APIView):
    """Counts by kind and your own reaction. PUT {kind} to react or change, DELETE to undo."""

    def _summary(self, request, key, obj):
        return selectors.reaction_summary(key, [obj.pk], request.user)[obj.pk]

    @extend_schema(responses=ReactionSummarySerializer)
    def get(self, request, key, pk):
        _, obj = registry.resolve(key, pk, request.user)
        return Response(self._summary(request, key, obj))

    @extend_schema(request=ReactionWriteSerializer, responses=ReactionSummarySerializer)
    def put(self, request, key, pk):
        _, obj = registry.resolve(key, pk, request.user)
        data = ReactionWriteSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        services.react(request.user, key, obj.pk, data.validated_data["kind"])
        return Response(self._summary(request, key, obj))

    @extend_schema(request=None, responses=ReactionSummarySerializer)
    def delete(self, request, key, pk):
        _, obj = registry.resolve(key, pk, request.user)
        services.unreact(request.user, key, obj.pk)
        return Response(self._summary(request, key, obj))
