import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.contenttypes.models import ContentType
from .models import Category, Tag, Share, Reaction, Attachment, Thread, UserActivity, UserStatistics, MarketingCampaign, LearningService, Analytics
from profiles.models import UserProfile
from posts.models import Post, Comment
from jobs.models import JobPost
from groups.models import Group

class ActivityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'activity_{self.room_name}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('type')
        
        if event_type == 'share':
            await self.handle_share(data)
        elif event_type == 'reaction':
            await self.handle_reaction(data)
        elif event_type == 'activity':
            await self.handle_activity(data)
        elif event_type == 'attachment':
            await self.handle_attachment(data)

    async def handle_share(self, data):
        user_id = data['user_id']
        content_type_id = data['content_type_id']
        object_id = data['object_id']
        shared_to_ids = data['shared_to']
        
        user = await sync_to_async(UserProfile.objects.get)(id=user_id)
        content_type = await sync_to_async(ContentType.objects.get)(id=content_type_id)
        content_object = await sync_to_async(content_type.get_object_for_this_type)(id=object_id)
        
        share = await sync_to_async(Share.objects.create)(
            user=user,
            content_type=content_type,
            object_id=object_id
        )
        
        for shared_to_id in shared_to_ids:
            shared_to_user = await sync_to_async(UserProfile.objects.get)(id=shared_to_id)
            await sync_to_async(share.shared_to.add)(shared_to_user)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'activity_share',
                'share': {
                    'user': user.user.username,
                    'content_object': str(content_object),
                    'shared_to': shared_to_ids,
                    'shared_at': str(share.shared_at)
                }
            }
        )
    
    async def handle_reaction(self, data):
        user_id = data['user_id']
        reaction_type = data['reaction_type']
        content_type_id = data['content_type_id']
        object_id = data['object_id']
        
        user = await sync_to_async(UserProfile.objects.get)(id=user_id)
        content_type = await sync_to_async(ContentType.objects.get)(id=content_type_id)
        content_object = await sync_to_async(content_type.get_object_for_this_type)(id=object_id)
        
        reaction = await sync_to_async(Reaction.objects.create)(
            user=user,
            type=reaction_type,
            content_type=content_type,
            object_id=object_id
        )
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'activity_reaction',
                'reaction': {
                    'user': user.user.username,
                    'reaction_type': reaction_type,
                    'content_object': str(content_object),
                    'timestamp': str(reaction.timestamp)
                }
            }
        )
    
    async def handle_activity(self, data):
        user_id = data['user_id']
        activity_type = data['activity_type']
        details = data['details']
        category_ids = data['categories']
        
        user = await sync_to_async(UserProfile.objects.get)(id=user_id)
        activity = await sync_to_async(UserActivity.objects.create)(
            user=user,
            activity_type=activity_type,
            details=details
        )
        
        for category_id in category_ids:
            category = await sync_to_async(Category.objects.get)(id=category_id)
            await sync_to_async(activity.categories.add)(category)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'activity_log',
                'activity': {
                    'user': user.user.username,
                    'activity_type': activity_type,
                    'details': details,
                    'categories': category_ids,
                    'timestamp': str(activity.timestamp)
                }
            }
        )
    
    async def handle_attachment(self, data):
        user_id = data['user_id']
        attachment_type = data['attachment_type']
        file_url = data['file_url']
        content_type_id = data['content_type_id']
        object_id = data['object_id']
        
        content_type = await sync_to_async(ContentType.objects.get)(id=content_type_id)
        content_object = await sync_to_async(content_type.get_object_for_this_type)(id=object_id)
        
        attachment = await sync_to_async(Attachment.objects.create)(
            attachment_type=attachment_type,
            file=file_url,
            content_type=content_type,
            object_id=object_id
        )
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'activity_attachment',
                'attachment': {
                    'attachment_type': attachment_type,
                    'file_url': file_url,
                    'content_object': str(content_object),
                    'timestamp': str(attachment.uploaded_at)
                }
            }
        )
    
    async def activity_share(self, event):
        await self.send(text_data=json.dumps({
            'type': 'share',
            'share': event['share']
        }))
    
    async def activity_reaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'reaction': event['reaction']
        }))
    
    async def activity_log(self, event):
        await self.send(text_data=json.dumps({
            'type': 'activity',
            'activity': event['activity']
        }))
    
    async def activity_attachment(self, event):
        await self.send(text_data=json.dumps({
            'type': 'attachment',
            'attachment': event['attachment']
        }))