"""One WebSocket per user. Services call `publish_to_user`; the SPA receives {event, data}."""

from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
from django.urls import path


def user_group(user_id) -> str:
    return f"user.{user_id}"


def publish_to_user(user_id, event: str, data: dict | None = None):
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        user_group(user_id), {"type": "push.event", "event": event, "data": data or {}}
    )


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

    async def push_event(self, message):
        await self.send_json({"event": message["event"], "data": message["data"]})


websocket_urlpatterns = [path("ws/events/", UserEventsConsumer.as_asgi())]
