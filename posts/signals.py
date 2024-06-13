# posts/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Post, Comment
from activity.models import Reaction, Tag, Share

# Signal to update post count for a user when a new post is created
@receiver(post_save, sender=Post)
def update_post_count(sender, instance, created, **kwargs):
    if created:
        user_profile = instance.author.userprofile
        user_profile.post_count += 1
        user_profile.save()

# Signal to update post count for a user when a post is deleted
@receiver(post_delete, sender=Post)
def decrease_post_count(sender, instance, **kwargs):
    user_profile = instance.author.userprofile
    if user_profile.post_count > 0:
        user_profile.post_count -= 1
        user_profile.save()

# Signal to update comment count for a post when a new comment is created
@receiver(post_save, sender=Comment)
def update_comment_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        post.comment_count += 1
        post.save()

# Signal to update comment count for a post when a comment is deleted
@receiver(post_delete, sender=Comment)
def decrease_comment_count(sender, instance, **kwargs):
    post = instance.post
    if post.comment_count > 0:
        post.comment_count -= 1
        post.save()

# Signal to update reaction count for a post when a new reaction is created
@receiver(post_save, sender=Reaction)
def update_reaction_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        post.reaction_count += 1
        post.save()

# Signal to update reaction count for a post when a reaction is deleted
@receiver(post_delete, sender=Reaction)
def decrease_reaction_count(sender, instance, **kwargs):
    post = instance.post
    if post.reaction_count > 0:
        post.reaction_count -= 1
        post.save()

# Signal to update share count for a post when a new share is created
@receiver(post_save, sender=Share)
def update_share_count(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        post.share_count += 1
        post.save()

# Signal to update share count for a post when a share is deleted
@receiver(post_delete, sender=Share)
def decrease_share_count(sender, instance, **kwargs):
    post = instance.post
    if post.share_count > 0:
        post.share_count -= 1
        post.save()

# Signal to handle tagging of users in comments
@receiver(post_save, sender=Comment)
def handle_comment_tagging(sender, instance, created, **kwargs):
    if created:
        # Your logic to handle tagging of users in comments
        pass

# Signal to handle tagging of posts with tags
@receiver(post_save, sender=Tag)
def handle_post_tagging(sender, instance, created, **kwargs):
    if created:
        # Your logic to handle tagging of posts with tags
        pass