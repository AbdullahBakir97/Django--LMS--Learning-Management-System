from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Certification
from profiles.models import User, UserProfile
from jobs.models import JobListing
from courses.models import Course
from notifications.models import Notification

# Signal to send notification when a new certification is created
@receiver(post_save, sender=Certification)
def send_certification_notification(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        notification_message = f"Congratulations! You have earned the {instance.name} certification."
        Notification.objects.create(user=user, message=notification_message)

# Signal to update related job listings when a user earns a new certification
@receiver(post_save, sender=Certification)
def update_related_jobs(sender, instance, created, **kwargs):
    if created:
        related_jobs = instance.related_jobs.all()
        for job in related_jobs:
            job.required_certifications.add(instance)

# Signal to update related courses when a user earns a new certification
@receiver(post_save, sender=Certification)
def update_related_courses(sender, instance, created, **kwargs):
    if created:
        related_courses = instance.related_courses.all()
        for course in related_courses:
            course.required_certifications.add(instance)

# Signal to update certification count when a certification is created or deleted
@receiver(post_save, sender=Certification)
@receiver(post_delete, sender=Certification)
def update_certification_count(sender, instance, **kwargs):
    user = instance.user
    user.certification_count = user.certifications.count()
    user.save()

# Signal to notify users when a certification is updated
@receiver(post_save, sender=Certification)
def notify_users_on_certification_update(sender, instance, **kwargs):
    if not instance.verification_status:
        user = instance.user
        notification_message = f"Your {instance.name} certification has been updated. Please verify your information."
        Notification.objects.create(user=user, message=notification_message)
