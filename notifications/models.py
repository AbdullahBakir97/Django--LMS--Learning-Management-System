from django.db import models
from profiles.models import UserProfile


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
    content = models.TextField()
    url = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.notification_type.type_name} Notification for {self.recipient.user.username}"

class NotificationTemplate(models.Model):
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    template = models.TextField()

    def __str__(self):
        return self.notification_type.type_name