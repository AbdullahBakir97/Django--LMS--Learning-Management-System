from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Event
from notifications.models import Notification

# Signal to send notification when a user is added to an event
@receiver(post_save, sender=Event)
def send_event_notification(sender, instance, created, **kwargs):
    if created:
        organizer = instance.organizer
        attendees = instance.attendees.exclude(id=organizer.id)  # Exclude organizer from attendees
        notification_message = f"You have been added to the event '{instance.title}' organized by {organizer.user.username}."
        Notification.objects.bulk_create([Notification(user=user, message=notification_message) for user in attendees])

# Signal to send notification when a user leaves an event
@receiver(post_delete, sender=Event.attendees.through)
def send_leave_event_notification(sender, instance, **kwargs):
    user = instance.userprofile
    event = instance.event
    notification_message = f"You have left the event '{event.title}'."
    Notification.objects.create(user=user, message=notification_message)

# Signal to update attendees count when a new attendee is added
@receiver(post_save, sender=Event.attendees.through)
def update_attendees_count(sender, instance, created, **kwargs):
    if created:
        event = instance.event
        event.attendees_count = event.attendees.count()
        event.save()