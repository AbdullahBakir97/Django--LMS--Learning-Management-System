from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import generics, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.fields import IntegerField
from rest_framework.response import Response

from . import selectors, services
from .models import Notification
from .serializers import NotificationSerializer, PreferenceSerializer

Count = inline_serializer("NotificationCount", {"count": IntegerField()})


@extend_schema(
    parameters=[OpenApiParameter("unread", OpenApiTypes.BOOL, description="Only unread (true)")]
)
class NotificationViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Your notifications, newest first. Other people's are invisible (404)."""

    queryset = Notification.objects.none()  # for the schema; get_queryset() scopes to the user

    serializer_class = NotificationSerializer
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        unread = self.request.query_params.get("unread")
        return selectors.notifications_for(
            self.request.user, unread=True if unread == "true" else None
        )

    @extend_schema(request=None, responses=NotificationSerializer)
    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = services.mark_read(request.user, self.get_object())
        return Response(self.get_serializer(notification).data)

    @extend_schema(request=None, responses=Count)
    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        return Response({"count": services.mark_all_read(request.user)})

    @extend_schema(responses=Count)
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        return Response({"count": selectors.unread_count(request.user)})


class PreferenceView(generics.RetrieveUpdateAPIView):
    """Email on or off, and which kinds you do not want at all."""

    serializer_class = PreferenceSerializer
    http_method_names = ["get", "patch", "put"]

    def get_object(self):
        return selectors.preference_for(self.request.user)
