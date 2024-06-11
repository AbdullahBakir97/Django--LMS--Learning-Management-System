import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import UserProfile, Skill, Experience, Education, Endorsement
from notifications.models import Notification

User = get_user_model()

class ProfileConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
        else:
            await self.channel_layer.group_add(
                f"user_{self.user.id}",
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if not self.user.is_anonymous:
            await self.channel_layer.group_discard(
                f"user_{self.user.id}",
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.handle_event(data)

    async def handle_event(self, event):
        # handle event based on type
        pass

    async def profile_notify(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def create_notification(self, user, message):
        Notification.objects.create(user=user, message=message)