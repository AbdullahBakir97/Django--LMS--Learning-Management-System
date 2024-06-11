from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Group, GroupMembership
from notifications.models import Notification

# Signal to send notifications when a user joins a group
@receiver(post_save, sender=GroupMembership)
def send_group_join_notification(sender, instance, created, **kwargs):
    if created:
        group = instance.group
        user = instance.user
        notification_message = f"You have joined the group '{group.name}'."
        Notification.objects.create(user=user, message=notification_message)

# Signal to send notifications when a user leaves a group
@receiver(post_delete, sender=GroupMembership)
def send_group_leave_notification(sender, instance, **kwargs):
    group = instance.group
    user = instance.user
    notification_message = f"You have left the group '{group.name}'."
    Notification.objects.create(user=user, message=notification_message)

# Signal to update group member count when a user joins or leaves a group
@receiver(post_save, sender=GroupMembership)
@receiver(post_delete, sender=GroupMembership)
def update_group_member_count(sender, instance, **kwargs):
    group = instance.group
    group.member_count = group.groupmembership_set.count()
    group.save()