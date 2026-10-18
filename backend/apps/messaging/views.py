from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.fields import IntegerField
from rest_framework.response import Response
from rest_framework.views import APIView

from . import selectors, services
from .models import Message
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    MessageWriteSerializer,
    StartSerializer,
)

User = get_user_model()


def _with_last(request, conversations) -> dict:
    ids = [c.last_message_id for c in conversations if c.last_message_id]
    last = {m.id: m for m in Message.objects.filter(id__in=ids).select_related("sender__profile")}
    return {"request": request, "last_messages": last}


class ConversationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Your conversations. Others' are 404."""

    serializer_class = ConversationSerializer
    lookup_value_regex = r"\d+"
    pagination_class = None  # shortcut: one list of your conversations; page it past a few hundred

    def get_queryset(self):
        return selectors.conversations_for(self.request.user)

    def list(self, request):
        rows = list(self.get_queryset())
        return Response(
            ConversationSerializer(rows, many=True, context=_with_last(request, rows)).data
        )

    def retrieve(self, request, pk=None):
        c = self.get_object()
        return Response(ConversationSerializer(c, context=_with_last(request, [c])).data)

    @extend_schema(request=StartSerializer, responses={201: ConversationSerializer})
    def create(self, request):
        data = StartSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        names = data.validated_data["usernames"]
        people = list(User.objects.filter(username__in=names, is_active=True))
        missing = set(names) - {u.username for u in people}
        if missing:
            raise Http404(f"No one called {', '.join(sorted(missing))}.")
        conversation = services.start(request.user, people, data.validated_data.get("title", ""))
        if data.validated_data.get("body"):
            services.send(request.user, conversation, data.validated_data["body"])
        c = self.get_queryset().get(pk=conversation.pk)
        return Response(
            ConversationSerializer(c, context=_with_last(request, [c])).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(request=None, responses={204: None})
    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        services.mark_read(request.user, self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(responses=inline_serializer("UnreadMessages", {"count": IntegerField()}))
    @action(detail=False, methods=["get"])
    def unread(self, request):
        return Response({"count": selectors.unread_total(request.user)})


class MessagesView(generics.ListCreateAPIView):
    """Newest first, cursor paged. POST {body} to send."""

    serializer_class = MessageSerializer

    def _conversation(self):
        p = selectors.participant(self.request.user, self.kwargs["pk"])
        if p is None:
            raise Http404
        return p.conversation

    def get_queryset(self):
        return selectors.messages_in(self._conversation().pk)

    @extend_schema(request=MessageWriteSerializer, responses={201: MessageSerializer})
    def post(self, request, pk):
        data = MessageWriteSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        message = services.send(request.user, self._conversation(), data.validated_data["body"])
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class MessageDetailView(APIView):
    def _message(self, request, pk):
        message = get_object_or_404(Message.objects.select_related("sender__profile"), pk=pk)
        if selectors.participant(request.user, message.conversation_id) is None:
            raise Http404
        return message

    @extend_schema(request=MessageWriteSerializer, responses=MessageSerializer)
    def patch(self, request, pk):
        data = MessageWriteSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        message = services.edit(
            request.user, self._message(request, pk), data.validated_data["body"]
        )
        return Response(MessageSerializer(message).data)

    @extend_schema(responses=MessageSerializer)
    def delete(self, request, pk):
        return Response(
            MessageSerializer(services.delete(request.user, self._message(request, pk))).data
        )
