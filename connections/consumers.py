import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ConnectionRequest, Connection, Recommendation
from profiles.models import UserProfile

class ConnectionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            self.room_name = f"user_{self.user.id}"
            self.room_group_name = f"user_{self.user.id}_notifications"
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event = data.get('event', None)
        
        if event == 'send_connection_request':
            await self.send_connection_request(data)
        elif event == 'accept_connection_request':
            await self.accept_connection_request(data)
        elif event == 'reject_connection_request':
            await self.reject_connection_request(data)
        elif event == 'send_recommendation':
            await self.send_recommendation(data)

    async def send_connection_request(self, data):
        from_user_id = data['from_user_id']
        to_user_id = data['to_user_id']
        
        from_user = await database_sync_to_async(UserProfile.objects.get)(id=from_user_id)
        to_user = await database_sync_to_async(UserProfile.objects.get)(id=to_user_id)
        
        connection_request = ConnectionRequest(from_user=from_user, to_user=to_user)
        await database_sync_to_async(connection_request.save)()

        await self.channel_layer.group_send(
            f"user_{to_user.id}_notifications",
            {
                'type': 'connection_request_received',
                'from_user': from_user.username,
                'to_user': to_user.username,
                'status': connection_request.status,
                'created_at': str(connection_request.created_at)
            }
        )

    async def accept_connection_request(self, data):
        request_id = data['request_id']
        connection_request = await database_sync_to_async(ConnectionRequest.objects.get)(id=request_id)
        
        await database_sync_to_async(connection_request.accept)()
        
        await self.channel_layer.group_send(
            f"user_{connection_request.from_user.id}_notifications",
            {
                'type': 'connection_request_accepted',
                'from_user': connection_request.from_user.username,
                'to_user': connection_request.to_user.username,
            }
        )

    async def reject_connection_request(self, data):
        request_id = data['request_id']
        connection_request = await database_sync_to_async(ConnectionRequest.objects.get)(id=request_id)
        
        await database_sync_to_async(connection_request.reject)()
        
        await self.channel_layer.group_send(
            f"user_{connection_request.from_user.id}_notifications",
            {
                'type': 'connection_request_rejected',
                'from_user': connection_request.from_user.username,
                'to_user': connection_request.to_user.username,
            }
        )

    async def send_recommendation(self, data):
        from_user_id = data['from_user_id']
        to_user_id = data['to_user_id']
        content = data['content']
        
        from_user = await database_sync_to_async(UserProfile.objects.get)(id=from_user_id)
        to_user = await database_sync_to_async(UserProfile.objects.get)(id=to_user_id)
        
        recommendation = Recommendation(recommended_by=from_user, recommended_user=to_user, content=content)
        await database_sync_to_async(recommendation.save)()
        
        await self.channel_layer.group_send(
            f"user_{to_user.id}_notifications",
            {
                'type': 'recommendation_received',
                'from_user': from_user.username,
                'to_user': to_user.username,
                'content': content,
            }
        )

    async def connection_request_received(self, event):
        await self.send(text_data=json.dumps({
            'event': 'connection_request_received',
            'from_user': event['from_user'],
            'to_user': event['to_user'],
            'status': event['status'],
            'created_at': event['created_at']
        }))
    
    async def connection_request_accepted(self, event):
        await self.send(text_data=json.dumps({
            'event': 'connection_request_accepted',
            'from_user': event['from_user'],
            'to_user': event['to_user']
        }))
    
    async def connection_request_rejected(self, event):
        await self.send(text_data=json.dumps({
            'event': 'connection_request_rejected',
            'from_user': event['from_user'],
            'to_user': event['to_user']
        }))
    
    async def recommendation_received(self, event):
        await self.send(text_data=json.dumps({
            'event': 'recommendation_received',
            'from_user': event['from_user'],
            'to_user': event['to_user'],
            'content': event['content']
        }))