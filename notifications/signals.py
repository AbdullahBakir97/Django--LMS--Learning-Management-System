from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from profiles.models import UserProfile
from .services import NotificationService

@receiver(post_save, sender=Notification)
def send_notification(sender, instance, created, **kwargs):
    if created:
        NotificationService.send_notification(instance)

@receiver(post_save, sender=UserProfile)
def create_default_notification_settings(sender, instance, created, **kwargs):
    if created:
        NotificationService.create_default_notification_settings(instance)