import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message
from notifications.models import Notification
from activity.models import Reaction, Attachment, Share
from profiles.models import UserProfile

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
        else:
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            self.room_group_name = f'chat_{self.room_id}'
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if not self.user.is_anonymous:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('type')
        
        if event_type == 'message':
            await self.handle_new_message(data)
        elif event_type == 'reaction':
            await self.handle_reaction(data)
        elif event_type == 'edit_message':
            await self.handle_edit_message(data)
        elif event_type == 'delete_message':
            await self.handle_delete_message(data)
        elif event_type == 'share_message':
            await self.handle_share_message(data)
        elif event_type == 'read_message':
            await self.handle_read_message(data)
        else:
            await self.send(json.dumps({'error': 'Invalid event type'}))

    async def handle_new_message(self, data):
        content = data.get('content')
        message_type = data.get('message_type', 'text')
        attachments = data.get('attachments', [])
        chat = await self.get_chat_by_id(self.room_id)
        
        if chat and content:
            message = await self.create_message(chat, content, message_type, attachments)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message.content,
                    'sender': self.user.username,
                    'message_type': message.message_type,
                    'attachments': attachments
                }
            )
            await self.create_notification(chat, message)

    async def handle_reaction(self, data):
        message_id = data.get('message_id')
        reaction_type = data.get('reaction_type')
        message = await self.get_message_by_id(message_id)
        
        if message and reaction_type:
            await self.add_reaction(message, reaction_type)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_reaction',
                    'message_id': message_id,
                    'reaction_type': reaction_type,
                    'reactor': self.user.username
                }
            )

    async def handle_edit_message(self, data):
        message_id = data.get('message_id')
        new_content = data.get('new_content')
        message = await self.get_message_by_id(message_id)
        
        if message and new_content:
            await self.edit_message(message, new_content)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'edit_message',
                    'message_id': message_id,
                    'new_content': new_content
                }
            )

    async def handle_delete_message(self, data):
        message_id = data.get('message_id')
        message = await self.get_message_by_id(message_id)
        
        if message:
            await self.delete_message(message)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'delete_message',
                    'message_id': message_id
                }
            )

    async def handle_share_message(self, data):
        message_id = data.get('message_id')
        shared_with_user_id = data.get('shared_with_user_id')
        message = await self.get_message_by_id(message_id)
        shared_with_user = await self.get_user_by_id(shared_with_user_id)
        
        if message and shared_with_user:
            await self.share_message(message, shared_with_user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'share_message',
                    'message_id': message_id,
                    'shared_with': shared_with_user.username
                }
            )

    async def handle_read_message(self, data):
        message_id = data.get('message_id')
        message = await self.get_message_by_id(message_id)
        
        if message:
            await self.mark_message_as_read(message)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_message',
                    'message_id': message_id,
                    'reader': self.user.username
                }
            )

    @database_sync_to_async
    def get_chat_by_id(self, chat_id):
        try:
            return ChatRoom.objects.get(pk=chat_id)
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def get_message_by_id(self, message_id):
        try:
            return Message.objects.get(pk=message_id)
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def create_message(self, chat, content, message_type, attachments):
        message = Message.objects.create(
            chat=chat,
            sender=self.user,
            content=content,
            message_type=message_type
        )
        for attachment in attachments:
            Attachment.objects.create(message=message, file=attachment)
        return message

    @database_sync_to_async
    def add_reaction(self, message, reaction_type):
        Reaction.objects.create(message=message, user=self.user, reaction_type=reaction_type)

    @database_sync_to_async
    def edit_message(self, message, new_content):
        message.content = new_content
        message.is_edited = True
        message.save()

    @database_sync_to_async
    def delete_message(self, message):
        message.is_deleted = True
        message.save()

    @database_sync_to_async
    def share_message(self, message, shared_with_user):
        Share.objects.create(message=message, shared_with=shared_with_user)

    @database_sync_to_async
    def mark_message_as_read(self, message):
        message.is_read = True
        message.save()

    @database_sync_to_async
    def create_notification(self, chat, message):
        for member in chat.members.all():
            if member != self.user:
                Notification.objects.create(
                    user=member.user,
                    message=f"New message from {self.user.username}: {message.content}"
                )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender': event['sender'],
            'message_type': event['message_type'],
            'attachments': event['attachments']
        }))

    async def message_reaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'message_id': event['message_id'],
            'reaction_type': event['reaction_type'],
            'reactor': event['reactor']
        }))

    async def edit_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'edit_message',
            'message_id': event['message_id'],
            'new_content': event['new_content']
        }))

    async def delete_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'delete_message',
            'message_id': event['message_id']
        }))

    async def share_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'share_message',
            'message_id': event['message_id'],
            'shared_with': event['shared_with']
        }))

    async def read_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_message',
            'message_id': event['message_id'],
            'reader': event['reader']
        }))