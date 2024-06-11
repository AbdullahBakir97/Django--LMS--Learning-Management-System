from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from profiles.models import UserProfile
from activity.models import Reaction, Share, Tag

NOTIFICATION_TYPE = [
    ('job_application', 'Job Application'),
    ('job_listing', 'Job Listing'),
    ('message', 'Message'),
    ('follow', 'Follow'),
    ('endorsement', 'Endorsement'),
    ('skill', 'Skill'),
    ('experience', 'Experience'),
    ('education', 'Education'),
    ('group', 'Group'),
]

class NotificationType(models.Model):
    type_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.type_name

class Notification(models.Model):
    recipient = models.ForeignKey(UserProfile, related_name='notifications', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    content = models.TextField()
    url = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    shares = models.ManyToManyField(Share, related_name='notifications', blank=True)
    priority = models.IntegerField(default=0)  # Priority of the notification
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.notification_type.type_name} Notification for {self.recipient.user.username}"

class NotificationTemplate(models.Model):
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    template = models.TextField()

    def __str__(self):
        return self.notification_type.type_name

class NotificationSettings(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.user.username}'s Notification Settings"

class NotificationReadStatus(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.user.username} read status for {self.notification}"
