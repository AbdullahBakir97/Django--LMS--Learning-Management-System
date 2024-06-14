from django.db import models
from django.conf import settings
from shortuuidfield import ShortUUIDField
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from taggit.managers import TaggableManager


class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name
    

    
    
class Share(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    shared_to = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='received_shares')
    attachments = GenericRelation('Attachment')
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'shared_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user.username} shared {self.content_object} to {self.shared_to.count()} users"

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.ForeignKey('messaging.Message', on_delete=models.CASCADE, null=True, blank=True)
    post = models.ForeignKey('posts.Post', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey('posts.Comment', on_delete=models.CASCADE, null=True, blank=True)
    job_post = models.ForeignKey('jobs.JobListing', on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, null=True, blank=True)
    
    
class Attachment(models.Model):
    PHOTO = 'photo'
    DOCUMENT = 'document'
    VIDEO = 'video'
    AUDIO = 'audio'
    OTHER = 'other'

    ATTACHMENT_TYPE_CHOICES = [
        (PHOTO, 'Photo'),
        (DOCUMENT, 'Document'),
        (VIDEO, 'Video'),
        (AUDIO, 'Audio'),
        (OTHER, 'Other'),
    ]

    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPE_CHOICES, default=PHOTO)
    file = models.FileField(upload_to='attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    def __str__(self):
        return f"Attachment for {self.content_object}"
    
    
class Thread(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='threads')
    subject = models.CharField(max_length=255)
    last_message_at = models.DateTimeField()

    def __str__(self):
        return self.subject
    
    
class UserActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField()
    categories = models.ManyToManyField(Category, related_name='user_activity_categories')

    def __str__(self):
        return f"{self.user.user.username} - {self.activity_type}"
    
    
class UserStatistics(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    connections_count = models.IntegerField(default=0)
    posts_count = models.IntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)

    def __str__(self):
        return f"Statistics for {self.user.user.username}"
    
    
class MarketingCampaign(models.Model):
    campaign_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    target_audience = models.TextField()
    categories = models.ManyToManyField(Category, related_name='marketing_categories')
    attachments = GenericRelation(Attachment)

    def __str__(self):
        return self.campaign_name
    
    
class LearningService(models.Model):
    service_name = models.CharField(max_length=100)
    description = models.TextField()
    categories = models.ManyToManyField(Category, related_name='learning_service_categories')
    resources = models.URLField()
    attachments = GenericRelation(Attachment)

    def __str__(self):
        return self.service_name
    
    
class Analytics(models.Model):
    activity_type = models.CharField(max_length=50)
    engagement_rate = models.FloatField(default=0.0)
    trending_topics = models.TextField()
    categories = models.ManyToManyField(Category, related_name='analytics_categories')

    def __str__(self):
        return self.activity_type