from django.utils import timezone
from .models import Notification, NotificationSettings, NotificationReadStatus

class NotificationService:
    @staticmethod
    def create_notification(recipient, content, notification_type, url, content_object, priority=0):
        notification = Notification.objects.create(
            recipient=recipient,
            content=content,
            notification_type=notification_type,
            url=url,
            content_object=content_object,
            priority=priority,
        )
        return notification

    @staticmethod
    def send_notification(notification):
        # Logic to send notification (e.g., via email, push notification, etc.)
        pass

    @staticmethod
    def mark_as_read(notification, user):
        read_status, created = NotificationReadStatus.objects.get_or_create(
            notification=notification,
            user=user
        )
        if not read_status.is_read:
            read_status.is_read = True
            read_status.read_at = timezone.now()
            read_status.save()
    
    @staticmethod
    def get_unread_notifications(user):
        return Notification.objects.filter(recipient=user, is_read=False)

    @staticmethod
    def update_notification_settings(user, notification_type, is_enabled):
        settings, created = NotificationSettings.objects.get_or_create(
            user=user,
            notification_type=notification_type
        )
        settings.is_enabled = is_enabled
        settings.save()
