from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from activity.models import Reaction, Share
from django.conf import settings

NOTIFICATION_TYPE = [
    ('job_application', 'Job Application'),
    ('job_listing', 'Job Listing'),
    ('message', 'Message'),
    ('follow', 'Follow'),
    ('connection', 'Connection'),
    ('reaction', 'Reaction'),
    ('post', 'Posts'),
    ('share', 'Share'),
    ('tag', 'Tag'),
    ('comment', 'Comment'),
    ('endorsement', 'Endorsement'),
    ('skill', 'Skill'),
    ('experience', 'Experience'),
    ('education', 'Education'),
    ('group', 'Group'),
]

class NotificationType(models.Model):
    PREDEFINED_TYPES = ['type1', 'type2']

    type_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.type_name

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    content = models.TextField()
    url = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    shares = models.ManyToManyField(Share, related_name='notifications_shares', blank=True)
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.notification_type.type_name} Notification for {self.recipient.username}"

class NotificationTemplate(models.Model):
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    template = models.TextField()

    def __str__(self):
        return self.notification_type.type_name

class NotificationSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.user.username}'s Notification Settings"

class NotificationReadStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.user.username} read status for {self.notification}"
