from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Follower, FollowRequest, FollowNotification
from notifications.models import Notification

# Signal to send notification when a user gains a new follower
@receiver(post_save, sender=Follower)
def send_follow_notification(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        follower = instance.follower
        notification_message = f"{follower.user.username} started following you."
        Notification.objects.create(user=user, message=notification_message)

# Signal to send notification when a follow request is accepted
@receiver(post_save, sender=FollowRequest)
def send_follow_request_notification(sender, instance, created, **kwargs):
    if not created and instance.status == 'accepted':
        from_user = instance.from_user
        to_user = instance.to_user
        notification_message = f"{from_user.user.username} has accepted your follow request."
        Notification.objects.create(user=to_user, message=notification_message)

# Signal to send notification when a follow request is received
@receiver(post_save, sender=FollowRequest)
def send_follow_request_received_notification(sender, instance, created, **kwargs):
    if created:
        from_user = instance.from_user
        to_user = instance.to_user
        notification_message = f"{from_user.user.username} wants to follow you."
        FollowNotification.objects.create(user=to_user, message=notification_message)

# Signal to update follow count when a new follower is added
@receiver(post_save, sender=Follower)
def update_follow_count(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        user.follow_count = Follower.objects.filter(user=user).count()
        user.save()