from django.db import models
from profiles.models import UserProfile
from groups.models import Group
from activity.models import Attachment, Reaction, Share, Tag, Category
from django.contrib.contenttypes.fields import GenericRelation

class Post(models.Model):
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, db_index=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts', null=True, blank=True, db_index=True)
    content = models.TextField()
    attachments = GenericRelation(Attachment)
    visibility = models.CharField(max_length=20, choices=[('public', 'Public'), ('private', 'Private')], default='public')
    categories = models.ManyToManyField(Category, related_name='posts_categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(UserProfile, related_name='liked_posts', blank=True, db_index=True)
    reactions = models.ManyToManyField(Reaction, related_name='post_reactions', blank=True, db_index=True)
    comments = models.ManyToManyField('Comment', related_name='post_comments', blank=True, db_index=True)
    shares = models.ManyToManyField(Share, related_name='post_shares', blank=True, db_index=True)
    tags = models.ManyToManyField(Tag,related_name='post_tags', null=True, db_index=True)

    def __str__(self):
        return self.content[:20]

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE, db_index=True)
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, db_index=True)
    content = models.TextField()
    attachments = GenericRelation(Attachment)
    visibility = models.CharField(max_length=20, choices=[('public', 'Public'), ('private', 'Private')], default='public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', db_index=True)
    reactions = models.ManyToManyField(Reaction, related_name='comment_reactions', blank=True, db_index=True)

    def __str__(self):
        return self.content[:20]


