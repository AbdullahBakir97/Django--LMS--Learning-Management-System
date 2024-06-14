from django.db import models
from profiles.models import UserProfile
from activity.models import Attachment, Category
from django.contrib.contenttypes.fields import GenericRelation
from taggit.managers import TaggableManager

class Event(models.Model):
    organizer = models.ForeignKey(UserProfile, related_name='organized_events', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    attachments = GenericRelation(Attachment)
    categories = models.ManyToManyField(Category, related_name='events_categoories')
    location = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    attendees = models.ManyToManyField(UserProfile, related_name='events', blank=True)
    event_date = models.DateField()
    capacity = models.PositiveIntegerField()
    tags = TaggableManager()

    def __str__(self):
        return f'{self.title} organized by {self.organizer.user.username}'