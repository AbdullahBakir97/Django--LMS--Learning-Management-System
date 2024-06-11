import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import UserProfile, Skill, Experience, Education, Endorsement
from followers.models import Follower, FollowRequest, FollowNotification
from notifications.models import Notification

User = get_user_model()

class ProfileConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if not self.user.is_anonymous:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('type')
        if event_type == 'follow':
            await self.handle_follow(data)
        elif event_type == 'unfollow':
            await self.handle_unfollow(data)
        elif event_type == 'endorse_skill':
            await self.handle_endorse_skill(data)
        elif event_type == 'profile_update':
            await self.handle_profile_update(data)
        elif event_type == 'send_message':
            await self.handle_send_message(data)
        else:
            await self.send(json.dumps({'error': 'Invalid event type'}))

    async def handle_follow(self, data):
        target_user_id = data.get('target_user_id')
        target_user = await self.get_user_by_id(target_user_id)
        if target_user:
            await self.follow_user(target_user.profile)
            await self.create_notification(target_user, f"{self.user.username} started following you.")
            await self.channel_layer.group_send(
                f"user_{target_user.id}",
                {
                    'type': 'profile_notify',
                    'message': f"{self.user.username} started following you."
                }
            )

    async def handle_unfollow(self, data):
        target_user_id = data.get('target_user_id')
        target_user = await self.get_user_by_id(target_user_id)
        if target_user:
            await self.unfollow_user(target_user.profile)
            await self.create_notification(target_user, f"{self.user.username} unfollowed you.")
            await self.channel_layer.group_send(
                f"user_{target_user.id}",
                {
                    'type': 'profile_notify',
                    'message': f"{self.user.username} unfollowed you."
                }
            )

    async def handle_endorse_skill(self, data):
        skill_id = data.get('skill_id')
        endorsed_user_id = data.get('endorsed_user_id')
        endorsed_user = await self.get_user_by_id(endorsed_user_id)
        if endorsed_user:
            skill = await self.get_skill_by_id(skill_id)
            if skill:
                await self.endorse_skill(skill, endorsed_user.profile)
                await self.create_notification(endorsed_user, f"{self.user.username} endorsed your skill {skill.name}.")
                await self.channel_layer.group_send(
                    f"user_{endorsed_user.id}",
                    {
                        'type': 'profile_notify',
                        'message': f"{self.user.username} endorsed your skill {skill.name}."
                    }
                )

    async def handle_profile_update(self, data):
        # Logic for handling profile updates
        pass

    async def handle_send_message(self, data):
        # Logic for handling sending messages
        pass

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_skill_by_id(self, skill_id):
        try:
            return Skill.objects.get(pk=skill_id)
        except Skill.DoesNotExist:
            return None

    @database_sync_to_async
    def follow_user(self, profile):
        self.user.profile.follow(profile)

    @database_sync_to_async
    def unfollow_user(self, profile):
        self.user.profile.unfollow(profile)

    @database_sync_to_async
    def endorse_skill(self, skill, profile):
        Endorsement.objects.create(skill=skill, endorsed_by=self.user.profile, endorsed_user=profile)

    @database_sync_to_async
    def create_notification(self, user, message):
        Notification.objects.create(user=user, message=message)

    async def profile_notify(self, event):
        await self.send(text_data=json.dumps(event))