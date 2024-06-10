from django.db import models
from profiles.models import UserProfile

class Event(models.Model):
    organizer = models.ForeignKey(UserProfile, related_name='organized_events', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    attendees = models.ManyToManyField(UserProfile, related_name='events', blank=True)
    event_date = models.DateField()
    capacity = models.PositiveIntegerField()
    category = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.title} organized by {self.organizer.user.username}'