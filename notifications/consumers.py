import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name = f"notifications_{self.scope['user'].username}"
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def send_notification(self, event):
        notification = event['notification']
        self.send(text_data=json.dumps({
            'type': notification['type'],
            'content': notification['content'],
            'url': notification['url'],
            'timestamp': notification['timestamp'],
        }))