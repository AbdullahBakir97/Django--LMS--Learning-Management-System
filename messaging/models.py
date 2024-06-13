from django.db import models
from shortuuidfield import ShortUUIDField
# from posts.models import Post, Comment
# from jobs.models import JobListing
# from groups.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
# from activity.models import Attachment, Reaction, Share, Tag
from django.conf import settings

class ChatRoom(models.Model):
    roomId = ShortUUIDField()
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chatrooms', db_index=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name if self.name else self.roomId

class Message(models.Model):
    TEXT = 'text'
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    FILE = 'file'

    MESSAGE_TYPE_CHOICES = [
        (TEXT, 'Text Message'),
        (IMAGE, 'Image Message'),
        (VIDEO, 'Video Message'),
        (AUDIO, 'Audio Message'),
        (FILE, 'File Attachment'),
    ]
    
    chat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, db_index=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default=TEXT)
    attachments = models.ManyToManyField('activity.Attachment', related_name='message_attachments', blank=True, db_index=True)
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    reactions = models.ManyToManyField('activity.Reaction', related_name='message_reactions', db_index=True)
    shares = models.ManyToManyField('activity.Share', related_name='message_shares', blank=True)
    
    

    def __str__(self):
        return f"{self.sender.user.username}: {self.content[:20]}"
    
    
    
# class ChatRoomNotification(models.Model):
#     chat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
#     user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     read = models.BooleanField(default=False)

#     def __str__(self):
#         return f'{self.user.user.username} received a notification for {self.chat.name}'