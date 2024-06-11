from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import JobListing, JobApplication, JobNotification
from notifications.models import Notification

# Signal to send notifications when a new job listing is posted
@receiver(post_save, sender=JobListing)
def send_job_listing_notification(sender, instance, created, **kwargs):
    if created:
        followers = instance.company.followers.all()
        notification_message = f"A new job listing '{instance.title}' is posted by {instance.company.name}."
        for follower in followers:
            Notification.objects.create(user=follower, message=notification_message)

# Signal to send notifications when a user applies for a job
@receiver(post_save, sender=JobApplication)
def send_job_application_notification(sender, instance, created, **kwargs):
    if created:
        job_listing = instance.job_listing
        company = job_listing.company
        notification_message = f"You have a new job application for the position '{job_listing.title}' from {instance.applicant.username}."
        Notification.objects.create(user=company.user, message=notification_message)

# Signal to send notifications when a job application status is updated
@receiver(post_save, sender=JobApplication)
def send_job_application_status_notification(sender, instance, **kwargs):
    if instance.status in ['accepted', 'rejected']:
        applicant = instance.applicant
        notification_message = f"Your job application status for the position '{instance.job_listing.title}' is updated to {instance.status}."
        Notification.objects.create(user=applicant, message=notification_message)

# Signal to send notifications when a new job notification is sent
@receiver(post_save, sender=JobNotification)
def send_job_notification(sender, instance, created, **kwargs):
    if created:
        recipients = instance.recipients.all()
        notification_message = f"You have a new job notification: {instance.message}."
        for recipient in recipients:
            Notification.objects.create(user=recipient, message=notification_message)

# Signal to update job listing count when a job listing is deleted
@receiver(post_delete, sender=JobListing)
def update_job_listing_count(sender, instance, **kwargs):
    company = instance.company
    company.job_listing_count -= 1
    company.save()