from django.db import models
from profiles.models import UserProfile
from groups.models import Group
from messaging.models import Reaction, Share, Tag

class Post(models.Model):
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(UserProfile, related_name='liked_posts', blank=True)
    reactions = models.ManyToManyField(Reaction, related_name='post_reactions', blank=True)
    comments = models.ManyToManyField('Comment', related_name='post_comments', blank=True)
    shares = models.ManyToManyField(Share, related_name='post_shares', blank=True)
    tags = models.ManyToManyField(Tag,related_name='post_tags', null=True)

    def __str__(self):
        return self.content[:20]

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    reactions = models.ManyToManyField(Reaction, related_name='comment_reactions', blank=True)

    def __str__(self):
        return self.content[:20]


