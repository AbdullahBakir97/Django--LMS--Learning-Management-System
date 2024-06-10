from django.db import models
from profiles.models import UserProfile
from shortuuidfield import ShortUUIDField

class ChatRoom(models.Model):
    roomId = ShortUUIDField()
    members = models.ManyToManyField(UserProfile, related_name='chatrooms')
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name if self.name else self.roomId

class Message(models.Model):
    chat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    message_type = models.CharField(max_length=20, choices=[('text', 'Text'), ('image', 'Image'), ('video', 'Video'), ('audio', 'Audio'), ('file', 'File')], default='text')
    attachments = models.FileField(upload_to='message_attachments/', blank=True, null=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    

    def __str__(self):
        return f"{self.sender.user.username}: {self.content[:20]}"
    
# class ChatRoomNotification(models.Model):
#     chat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
#     user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     read = models.BooleanField(default=False)

#     def __str__(self):
#         return f'{self.user.user.username} received a notification for {self.chat.name}'