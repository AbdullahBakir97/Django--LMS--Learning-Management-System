from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User, UserProfile, Skill, Experience, Education, Endorsement
from notifications.models import Notification
from connections.models import Connection

# Signal to create a user profile when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Signal to save the user profile when the user is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

# Signal to update the endorsement count when an endorsement is created
@receiver(post_save, sender=Endorsement)
def update_endorsement_count(sender, instance, created, **kwargs):
    if created:
        skill = instance.skill
        skill.endorsement_count += 1
        skill.save()

# Signal to decrease the endorsement count when an endorsement is deleted
@receiver(post_delete, sender=Endorsement)
def decrease_endorsement_count(sender, instance, **kwargs):
    skill = instance.skill
    skill.endorsement_count -= 1
    skill.save()

# Signal to send notifications when skills are endorsed
@receiver(post_save, sender=Endorsement)
def send_endorsement_notification(sender, instance, created, **kwargs):
    if created:
        skill_owner = instance.skill.user_profile.user
        notification_message = f"Your skill '{instance.skill.name}' has been endorsed by {instance.endorsed_by.userprofile.get_full_name()}"
        Notification.objects.create(user=skill_owner, message=notification_message)

# Signal to update the completion percentage of user profiles
@receiver(post_save, sender=[Experience, Education])
def update_profile_completion(sender, instance, created, **kwargs):
    profile = instance.user_profile
    profile.calculate_completion_percentage()
    profile.save()

# Signal to cascade delete related profile data when a user is deleted
@receiver(post_delete, sender=User)
def delete_related_profile_data(sender, instance, **kwargs):
    instance.userprofile.delete()

# Signal to send notifications when new connections are made
@receiver(post_save, sender=Connection)
def send_connection_notification(sender, instance, created, **kwargs):
    if created:
        notification_message = f"{instance.user.get_full_name()} has connected with you."
        Notification.objects.create(user=instance.connection, message=notification_message)

# Signal to log changes made to user profiles for auditing purposes
@receiver(post_save, sender=UserProfile)
def log_profile_changes(sender, instance, created, **kwargs):
    if not created:
        # Log profile changes here
        pass

# Signal to send notifications when new experiences or educations are added to a profile
@receiver(post_save, sender=[Experience, Education])
def send_profile_update_notification(sender, instance, created, **kwargs):
    if created:
        notification_message = f"New {sender.__name__} added to your profile."
        Notification.objects.create(user=instance.user_profile.user, message=notification_message)

# Signal to update the rank of skills based on endorsements or other criteria
@receiver(post_save, sender=Endorsement)
def update_skill_rank(sender, instance, created, **kwargs):
    if created:
        # Implement logic to update skill rank
        instance.skill.update_rank()
        print(f"Skill rank updated for skill: {instance.skill.name}")
        

# Signal to trigger actions when a user changes their profile picture
@receiver(post_save, sender=UserProfile)
def profile_picture_updated(sender, instance, created, **kwargs):
    if not created and instance.picture != instance._picture:
        # Implement actions such as resizing, cropping, or updating references to the new picture
        instance.resize_profile_picture()
        print(f"Profile picture updated for user: {instance.user.username}")
        

# Signal to trigger actions when a user changes the visibility settings of their profile
@receiver(post_save, sender=UserProfile)
def profile_visibility_changed(sender, instance, created, **kwargs):
    if not created and instance.visibility != instance._visibility:
        # Implement actions such as updating visibility flags or notifying connected users
        instance.update_visibility()
        print(f"Profile visibility changed for user: {instance.user.username}")

# Signal to send notifications when skills receive endorsements
@receiver(post_save, sender=Endorsement)
def send_skill_endorsement_notification(sender, instance, created, **kwargs):
    if created:
        notification_message = f"{instance.endorsed_by.userprofile.get_full_name()} has endorsed your skill '{instance.skill.name}'."
        Notification.objects.create(user=instance.skill.user_profile.user, message=notification_message)

# Signal to send notifications when new experiences or educations are added to a profile
@receiver(post_save, sender=[Experience, Education])
def send_profile_update_notification(sender, instance, created, **kwargs):
    if created:
        notification_message = f"New {sender.__name__} added to your profile."
        Notification.objects.create(user=instance.user_profile.user, message=notification_message)

# Signal to track and log changes made to user profiles for auditing purposes
@receiver(post_save, sender=UserProfile)
def log_profile_changes(sender, instance, created, **kwargs):
    if not created:
        # Log profile changes here
        pass

# Signal to send notifications when a user connects with another user
@receiver(post_save, sender=Connection)
def send_connection_notification(sender, instance, created, **kwargs):
    if created:
        notification_message = f"{instance.user.get_full_name()} has connected with you."
        Notification.objects.create(user=instance.connection, message=notification_message)

# Signal to send notifications when skills are endorsed
@receiver(post_save, sender=Endorsement)
def send_endorsement_notification(sender, instance, created, **kwargs):
    if created:
        skill_owner = instance.skill.user_profile.user
        notification_message = f"Your skill '{instance.skill.name}' has been endorsed by {instance.endorsed_by.userprofile.get_full_name()}"
        Notification.objects.create(user=skill_owner, message=notification_message)