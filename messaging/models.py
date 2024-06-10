from django.db import models
from profiles.models import UserProfile
from shortuuidfield import ShortUUIDField
from posts.models import Post, Comment
from jobs.models import JobPost
from groups.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Share(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    shared_to = models.ManyToManyField(UserProfile, related_name='received_shares')

    def __str__(self):
        return f"{self.user.user.username} shared {self.content_object} to {self.shared_to.all().count()} users"

class Reaction(models.Model):
    REACTION_CHOICES = [
        ('like', 'Like'),
        ('heart', 'Heart'),
        ('laugh', 'Laugh'),
        ('wow', 'Wow'),
        ('sad', 'Sad'),
        ('insight', 'Insight')
    ]
    type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.ForeignKey('Message', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    
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
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    reactions = models.ManyToManyField(Reaction, related_name='message_reactions')
    shares = models.ManyToManyField(Share, related_name='message_shares', blank=True)
    
    

    def __str__(self):
        return f"{self.sender.user.username}: {self.content[:20]}"
    
# class ChatRoomNotification(models.Model):
#     chat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
#     user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     read = models.BooleanField(default=False)

#     def __str__(self):
#         return f'{self.user.user.username} received a notification for {self.chat.name}'