from django.db import models
from profiles.models import UserProfile
from activity.models import Reaction, Share, Tag, Category

class Group(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    categories = models.ManyToManyField(Category, related_name='groupes_categories')
    members = models.ManyToManyField(UserProfile, through='GroupMembership', related_name='groups')
    created_at = models.DateTimeField(auto_now_add=True)
    group_type = models.CharField(max_length=20, choices=[('public', 'Public'), ('private', 'Private')], default='public')
    privacy_level = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium')
    tags = models.CharField(max_length=100, blank=True)
    cover_image = models.ImageField(upload_to='group_covers/', blank=True, null=True)
    shares = models.ManyToManyField(Share, related_name='group_shares', blank=True)
    tags = models.ManyToManyField(Tag, related_name='tagged_groups', blank=True)

    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('member', 'Member')], default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.username} in {self.group.name}"