from django.contrib.contenttypes.models import ContentType
from .models import Notification, NotificationType, NotificationSettings, NotificationReadStatus
from profiles.models import User ,UserProfile
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class NotificationService:
    @staticmethod
    def create_notification(recipient, content, notification_type_name, url, content_object, priority=0):
        notification_type, created = NotificationType.objects.get_or_create(type_name=notification_type_name)
        content_type = ContentType.objects.get_for_model(content_object)

        # Check if notifications of this type are enabled for the user
        if not NotificationService.is_notification_enabled(recipient, notification_type):
            return None

        notification = Notification.objects.create(
            recipient=recipient,
            content=content,
            notification_type=notification_type,
            url=url,
            content_object=content_object,
            content_type=content_type,
            object_id=content_object.id,
            priority=priority,
        )
        return notification

    @staticmethod
    def send_notification(notification):
        # Logic to send notification (e.g., via email, push notification, etc.)
        # Implement as needed, possibly using external services
        
        # Send Web Push Notification
        # NotificationService.send_web_push(notification)

        # Send real-time notification using WebSockets
        NotificationService.send_websocket_notification(notification)

    # @staticmethod
    # def send_web_push(notification):
    #     subscription_info = notification.recipient.userprofile.webpush_subscription
    #     if subscription_info:
    #         payload = {
    #             'title': notification.notification_type.type_name,
    #             'body': notification.content,
    #             'url': notification.url
    #         }
    #         try:
    #             webpush(
    #                 subscription_info=subscription_info,
    #                 data=json.dumps(payload),
    #                 vapid_private_key='',
    #                 vapid_claims={
    #                     "sub": "EMAIL@example.com"
    #                 }
    #             )
    #         except WebPushException as ex:
    #             print(f"Web push failed: {ex}")

    @staticmethod
    def send_websocket_notification(notification):
        channel_layer = get_channel_layer()
        group_name = f"notifications_{notification.recipient.username}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_notification',
                'notification': {
                    'type': notification.notification_type.type_name,
                    'content': notification.content,
                    'url': notification.url,
                    'timestamp': str(notification.timestamp),
                }
            }
        )

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
    def mark_all_as_read(user):
        unread_notifications = Notification.objects.filter(recipient=user, is_read=False)
        for notification in unread_notifications:
            NotificationService.mark_as_read(notification, user)

    @staticmethod
    def get_unread_notifications(user):
        return Notification.objects.filter(recipient=user, is_read=False)
    
    @staticmethod
    def create_default_notification_settings(instance):
        
    # Assuming PREDEFINED_TYPES is a list of type names
        if not isinstance(instance, User):
            raise ValueError("Expected instance to be a User instance.")

        default_settings = NotificationType.PREDEFINED_TYPES

        user = instance

        for type_name in default_settings:
            notification_type, created = NotificationType.objects.get_or_create(type_name=type_name)

            # Make sure user is a User instance and not a string or other type
            Notification.objects.get_or_create(recipient=user, notification_type=notification_type)
            
    @staticmethod
    def add_notification_setting(user, type_name):
        notification_type, created = NotificationType.objects.get_or_create(type_name=type_name)
        Notification.objects.get_or_create(user=user, notification_type=notification_type)

        @staticmethod
        def update_notification_settings(user, notification_type_name, is_enabled):
            notification_type, created = NotificationType.objects.get_or_create(type_name=notification_type_name)
            settings, created = NotificationSettings.objects.get_or_create(
                user=user,
                notification_type=notification_type
            )
            settings.is_enabled = is_enabled
            settings.save()

    @staticmethod
    def is_notification_enabled(user, notification_type):
        try:
            setting = NotificationSettings.objects.get(user=user, notification_type=notification_type)
            return setting.is_enabled
        except NotificationSettings.DoesNotExist:
            return True

    @staticmethod
    def get_notifications(user, limit=10):
        return Notification.objects.filter(recipient=user).order_by('-timestamp')[:limit]
