from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Company, CompanyUpdate
from profiles.models import User, UserProfile
from notifications.models import Notification, NotificationType

# Signal to create a company profile when a new user is created
@receiver(post_save, sender=UserProfile)
def create_company_profile(sender, instance, created, **kwargs):
    if created:
        Company.objects.create(name=f"{instance.user.username}'s Company")

# Signal to send notification when a new company update is created
@receiver(post_save, sender=CompanyUpdate)
def send_company_update_notification(sender, instance, created, **kwargs):
    if created:
        company_followers = instance.company.followers.all()
        notification_message = f"New update from {instance.company.name}: {instance.title}"
        for follower in company_followers:
            Notification.objects.create(user=follower, message=notification_message)

# Signal to update follower count when a user follows or unfollows a company
@receiver(post_save, sender=Company.followers.through)
@receiver(post_delete, sender=Company.followers.through)
def update_follower_count(sender, instance, **kwargs):
    company = instance.company
    company.follower_count = company.followers.count()
    company.save()

# Signal to update company member count when a user joins or leaves a company
@receiver(post_save, sender=Company.members.through)
@receiver(post_delete, sender=Company.members.through)
def update_member_count(sender, instance, **kwargs):
    company = instance.company
    company.member_count = company.members.count()
    company.save()

# Signal to delete associated company updates when a company is deleted
@receiver(post_save, sender=Company)
def notify_admins_on_company_creation(sender, instance, created, **kwargs):
    if created:
        notification_message = f"A new company '{instance.name}' has been created."
        notification_type = NotificationType.objects.get_or_create(type_name='company_creation')[0]
        admin_profiles = UserProfile.objects.filter(user__is_staff=True)

        for admin_profile in admin_profiles:
            Notification.objects.create(
                recipient=admin_profile.user,
                content_object=instance,
                content=notification_message,
                url=f'/companies/{instance.id}/',
                notification_type=notification_type
            )