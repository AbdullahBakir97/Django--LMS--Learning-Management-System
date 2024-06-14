from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from .models import User, UserProfile, Skill, Experience, Education, Endorsement
from notifications.services import NotificationService, Notification, NotificationType
from connections.models import Connection

# Signal to create a UserProfile when a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        NotificationService.create_default_notification_settings(instance)


@receiver(post_save, sender=UserProfile)
def create_default_notification_settings(sender, instance, created, **kwargs):
    """
    Signal handler to create default notification settings for a new UserProfile.
    """
    if created:
        if not isinstance(instance.user, User):
            raise ValueError("Expected UserProfile's user field to be a User instance.")
        
        user = instance.user
        
        # Assuming PREDEFINED_TYPES is a list of type names for notifications
        default_settings = NotificationType.PREDEFINED_TYPES
        
        for type_name in default_settings:
            notification_type, _ = NotificationType.objects.get_or_create(type_name=type_name)
            
            # Create default notification settings for the user
            Notification.objects.get_or_create(recipient=user, notification_type=notification_type)

# Signal to update the endorsement count when an Endorsement is created
@receiver(post_save, sender=Endorsement)
def update_endorsement_count(sender, instance, created, **kwargs):
    if created:
        instance.skill.refresh_from_db()
        instance.skill.endorsement_count = F('endorsement_count') + 1
        instance.skill.save(update_fields=['endorsement_count'])

# Signal to decrease the endorsement count when an Endorsement is deleted
@receiver(post_delete, sender=Endorsement)
def decrease_endorsement_count(sender, instance, **kwargs):
    instance.skill.refresh_from_db()
    instance.skill.endorsement_count = F('endorsement_count') - 1
    instance.skill.save(update_fields=['endorsement_count'])

# Signal to send notifications when skills are endorsed
@receiver(post_save, sender=Endorsement)
def send_endorsement_notification(sender, instance, created, **kwargs):
    if created:
        NotificationService.create_notification(
            recipient=instance.skill.user_profile,
            content=f"Your skill '{instance.skill.name}' has been endorsed by {instance.endorsed_by.userprofile.get_full_name()}",
            notification_type_name='endorsement',
            content_object=instance,
            priority=0
        )

# Signal to update the completion percentage of user profiles
@receiver(post_save, sender=[Experience, Education])
def update_profile_completion(sender, instance, created, **kwargs):
    instance.user_profile.calculate_completion_percentage()
    instance.user_profile.save()

# Signal to cascade delete related profile data when a user is deleted
@receiver(post_delete, sender=User)
def delete_related_profile_data(sender, instance, **kwargs):
    instance.userprofile.delete()

# Signal to send notifications when new experiences or educations are added to a profile
@receiver(post_save, sender=[Experience, Education])
def send_profile_update_notification(sender, instance, created, **kwargs):
    if created:
        NotificationService.create_notification(
            recipient=instance.user_profile.user,
            content=f"New {sender.__name__} added to your profile.",
            notification_type_name='profile_update',
            content_object=instance,
            priority=0
        )

# Signal to log changes made to user profiles for auditing purposes
@receiver(post_save, sender=UserProfile)
def log_profile_changes(sender, instance, created, **kwargs):
    if not created:
        # Implement logging of profile changes here
        pass

# Signal to update the rank of skills based on endorsements or other criteria
@receiver(post_save, sender=Endorsement)
def update_skill_rank(sender, instance, created, **kwargs):
    if created:
        instance.skill.update_rank()

# Signal to trigger actions when a user changes their profile picture
@receiver(post_save, sender=UserProfile)
def profile_picture_updated(sender, instance, created, **kwargs):
    if not created and instance.profile_picture != instance.profile_picture:
        instance.resize_profile_picture()

# Signal to trigger actions when a user changes the visibility settings of their profile
@receiver(post_save, sender=UserProfile)
def profile_visibility_changed(sender, instance, created, **kwargs):
    if not created and instance.visibility != instance._visibility:
        instance.update_visibility()

# Signal to send notifications when skills receive endorsements
@receiver(post_save, sender=Endorsement)
def send_skill_endorsement_notification(sender, instance, created, **kwargs):
    if created:
        NotificationService.create_notification(
            recipient=instance.endorsed_by.userprofile,
            content=f"{instance.endorsed_by.userprofile.get_full_name()} has endorsed your skill '{instance.skill.name}'.",
            notification_type_name='skill_endorsement',
            content_object=instance,
            priority=0
        )

# Signal to send notifications when a user connects with another user
@receiver(post_save, sender=Connection)
def send_connection_notification(sender, instance, created, **kwargs):
    if created:
        NotificationService.create_notification(
            recipient=instance.connection,
            content=f"{instance.user.get_full_name()} has connected with you.",
            notification_type_name='connection',
            content_object=instance,
            priority=0
        )

