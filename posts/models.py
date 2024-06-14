from django.db import models
from django.conf import settings
# from groups.models import Group
from activity.models import Attachment
from django.contrib.contenttypes.fields import GenericRelation
from taggit.managers import TaggableManager

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='posts', null=True, blank=True, db_index=True)
    content = models.TextField(max_length=5000)
    attachments = GenericRelation(Attachment)
    visibility = models.CharField(max_length=20, choices=[('public', 'Public'), ('private', 'Private')], default='public')
    categories = models.ManyToManyField('activity.Category', related_name='posts_categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_posts', blank=True, db_index=True)
    reactions = models.ManyToManyField('activity.Reaction', related_name='post_reactions', blank=True, db_index=True)
    comments = models.ManyToManyField('Comment', related_name='post_comments', blank=True, db_index=True)
    shares = models.ManyToManyField('activity.Share', related_name='post_shares', blank=True, db_index=True)
    tags = TaggableManager()

    def __str__(self):
        return self.content[:20]

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments_posts', on_delete=models.CASCADE, db_index=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    content = models.TextField(max_length=2000)
    attachments = GenericRelation(Attachment)
    visibility = models.CharField(max_length=20, choices=[('public', 'Public'), ('private', 'Private')], default='public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', db_index=True)
    reactions = models.ManyToManyField('activity.Reaction', related_name='comment_reactions', blank=True, db_index=True)

    def __str__(self):
        return self.content[:20]


