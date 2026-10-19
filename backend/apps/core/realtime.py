"""One WebSocket per user. Services call `publish_to_user`; the SPA receives {event, data}.

The SPA authenticates with a bearer token it keeps in memory, which a browser cannot attach to
a WebSocket. So it asks `POST /api/realtime/ticket/` for a signed ticket that lives 30 seconds
and connects to `/ws/events/?ticket=...`. The access token never appears in a URL or a log.
"""

import json
import logging
import time
from urllib.parse import parse_qs

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import signing
from django.urls import path

logger = logging.getLogger(__name__)

_inbound: dict = {}
TYPING_INTERVAL = 2.0


def on_client_message(kind: str):
    """Register a handler for {"type": kind, ...} frames the SPA sends up the socket.

    Handlers run in a thread with database access: handler(user, payload). Upper contexts
    register here from AppConfig.ready(), so core never imports them.
    """

    def decorator(handler):
        _inbound[kind] = handler
        return handler

    return decorator


TICKET_SALT = "realtime.ticket"
TICKET_MAX_AGE = 30


def issue_ticket(user) -> str:
    return signing.dumps(user.pk, salt=TICKET_SALT)


@database_sync_to_async
def _user_for_ticket(ticket: str):
    try:
        user_id = signing.loads(ticket, salt=TICKET_SALT, max_age=TICKET_MAX_AGE)
    except signing.BadSignature:  # also covers SignatureExpired
        return AnonymousUser()
    return get_user_model().objects.filter(pk=user_id, is_active=True).first() or AnonymousUser()


class TicketAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        ticket = query.get("ticket", [""])[0]
        scope["user"] = await _user_for_ticket(ticket) if ticket else AnonymousUser()
        return await super().__call__(scope, receive, send)


def user_group(user_id) -> str:
    return f"user.{user_id}"


def publish_to_user(user_id, event: str, data: dict | None = None):
    """Best effort: the write already committed, so a channel-layer outage is logged, not raised."""
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(
            user_group(user_id), {"type": "push.event", "event": event, "data": data or {}}
        )
    except Exception:
        logger.exception("realtime push failed", extra={"event": event, "user_id": user_id})


class UserEventsConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close(code=4401)
            return
        self.group = user_group(user.id)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    @classmethod
    async def decode_json(cls, text_data):
        try:
            return json.loads(text_data)
        except (TypeError, ValueError):
            return None  # a malformed frame is dropped, not fatal to the connection

    async def receive_json(self, content, **kwargs):
        handler = _inbound.get(content.get("type")) if isinstance(content, dict) else None
        if handler is None:
            return
        if content["type"] == "typing":
            # Each frame costs queries and a fan-out to every participant: one per 2 seconds.
            now = time.monotonic()
            if now - getattr(self, "_last_typing", 0.0) < TYPING_INTERVAL:
                return
            self._last_typing = now
        try:
            await database_sync_to_async(handler)(self.scope["user"], content)
        except Exception:
            logger.exception("client message failed", extra={"type": content.get("type")})

    async def push_event(self, message):
        await self.send_json({"event": message["event"], "data": message["data"]})


websocket_urlpatterns = [path("ws/events/", UserEventsConsumer.as_asgi())]
