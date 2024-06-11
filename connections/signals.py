from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ConnectionRequest, Connection, Recommendation
from notifications.models import Notification

# Signal to send notification when a connection request is sent
@receiver(post_save, sender=ConnectionRequest)
def send_connection_request_notification(sender, instance, created, **kwargs):
    if created:
        to_user = instance.to_user.user
        from_user = instance.from_user.userprofile
        notification_message = f"{from_user} wants to connect with you."
        Notification.objects.create(user=to_user, message=notification_message)

# Signal to send notification when a connection request is accepted
@receiver(post_save, sender=ConnectionRequest)
def send_connection_accept_notification(sender, instance, created, **kwargs):
    if not created and instance.status == 'accepted':
        to_user = instance.from_user.user
        from_user = instance.to_user.userprofile
        notification_message = f"{from_user} accepted your connection request."
        Notification.objects.create(user=to_user, message=notification_message)

# Signal to establish connection when a connection request is accepted
@receiver(post_save, sender=ConnectionRequest)
def establish_connection(sender, instance, created, **kwargs):
    if not created and instance.status == 'accepted':
        Connection.objects.create(user=instance.from_user, connection=instance.to_user)

# Signal to send recommendation notification
@receiver(post_save, sender=Recommendation)
def send_recommendation_notification(sender, instance, created, **kwargs):
    if created:
        recommended_user = instance.recommended_user.user
        recommended_by = instance.recommended_by.userprofile
        notification_message = f"{recommended_by} recommended you."
        Notification.objects.create(user=recommended_user, message=notification_message)

# Signal to update connection count when a new connection is established
@receiver(post_save, sender=Connection)
def update_connection_count(sender, instance, created, **kwargs):
    if created:
        user = instance.user.userprofile
        user.connection_count = Connection.objects.filter(user=user).count()
        user.save()

# Signal to delete associated connection requests when a connection is deleted
@receiver(post_delete, sender=Connection)
def delete_associated_connection_requests(sender, instance, **kwargs):
    ConnectionRequest.objects.filter(from_user=instance.user).delete()
