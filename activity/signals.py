from django.db import models
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from profiles.models import UserProfile
from posts.models import Post, Comment
from jobs.models import JobListing
from groups.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from .models import Category, Share, Reaction, Attachment, Thread, UserActivity, UserStatistics, MarketingCampaign, LearningService, Analytics


@receiver(post_save, sender=Post)
def post_activity(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(
            user=instance.author,
            activity_type='post_created',
            details=f'Created a new post: {instance.title}'
        )
    else:
        UserActivity.objects.create(
            user=instance.author,
            activity_type='post_updated',
            details=f'Updated a post: {instance.title}'
        )

@receiver(post_delete, sender=Post)
def post_deleted_activity(sender, instance, **kwargs):
    UserActivity.objects.create(
        user=instance.author,
        activity_type='post_deleted',
        details=f'Deleted a post: {instance.title}'
    )

@receiver(post_save, sender=Comment)
def comment_activity(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(
            user=instance.author,
            activity_type='comment_created',
            details=f'Commented on a post: {instance.post.title}'
        )
    else:
        UserActivity.objects.create(
            user=instance.author,
            activity_type='comment_updated',
            details=f'Updated a comment on a post: {instance.post.title}'
        )

@receiver(post_delete, sender=Comment)
def comment_deleted_activity(sender, instance, **kwargs):
    UserActivity.objects.create(
        user=instance.author,
        activity_type='comment_deleted',
        details=f'Deleted a comment on a post: {instance.post.title}'
    )

@receiver(post_save, sender=Reaction)
def reaction_activity(sender, instance, created, **kwargs):
    if created:
        content_object = instance.content_object
        UserActivity.objects.create(
            user=instance.user,
            activity_type=f'{instance.get_type_display()}_reaction',
            details=f'Reacted to {content_object}'
        )

@receiver(post_save, sender=Share)
def share_activity(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(
            user=instance.user,
            activity_type='content_shared',
            details=f'Shared content: {instance.content_object}'
        )

@receiver(post_save, sender=Attachment)
def attachment_activity(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(
            user=instance.content_object.user,
            activity_type='attachment_added',
            details=f'Added an attachment to {instance.content_object}'
        )

@receiver(post_save, sender=Thread)
def thread_activity(sender, instance, created, **kwargs):
    if created:
        for participant in instance.participants.all():
            UserActivity.objects.create(
                user=participant,
                activity_type='thread_created',
                details=f'Joined a new thread: {instance.subject}'
            )

@receiver(post_save, sender=UserStatistics)
def user_statistics_updated(sender, instance, **kwargs):
    UserActivity.objects.create(
        user=instance.user,
        activity_type='statistics_updated',
        details='User statistics updated'
    )

@receiver(post_save, sender=MarketingCampaign)
def marketing_campaign_activity(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(
            user=instance.user,
            activity_type='marketing_campaign_created',
            details=f'Created marketing campaign: {instance.campaign_name}'
        )
    else:
        UserActivity.objects.create(
            user=instance.user,
            activity_type='marketing_campaign_updated',
            details=f'Updated marketing campaign: {instance.campaign_name}'
        )

@receiver(post_save, sender=LearningService)
def learning_service_activity(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(
            user=instance.user,
            activity_type='learning_service_created',
            details=f'Created learning service: {instance.service_name}'
        )
    else:
        UserActivity.objects.create(
            user=instance.user,
            activity_type='learning_service_updated',
            details=f'Updated learning service: {instance.service_name}'
        )

@receiver(post_save, sender=Analytics)
def analytics_activity(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(
            user=instance.user,
            activity_type='analytics_created',
            details='Created new analytics'
        )
    else:
        UserActivity.objects.create(
            user=instance.user,
            activity_type='analytics_updated',
            details='Updated analytics'
        )

@receiver(m2m_changed, sender=Share.shared_to.through)
def share_recipients_changed(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove']:
        UserActivity.objects.create(
            user=instance.user,
            activity_type='share_recipients_changed',
            details=f'Updated share recipients for content: {instance.content_object}'
        )