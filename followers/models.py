from django.db import models
from django.utils import timezone
from django.conf import settings

class Follower(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_followers', on_delete=models.CASCADE)
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_following', on_delete=models.CASCADE)
    followed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.follower.user.username} follows {self.user.user.username}"
    
    @staticmethod
    def is_follower(user, follower):
        return Follower.objects.filter(user=user, follower=follower).exists()

    @staticmethod
    def get_followers(user):
        return Follower.objects.filter(user=user)

class FollowRequest(models.Model):
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='follow_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='follow_requests_received', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.from_user.user.username} wants to follow {self.to_user.user.username}"

    def accept(self):
        self.status = 'accepted'
        Follower.objects.create(user=self.to_user, follower=self.from_user)
        self.save()

    def reject(self):
        self.status = 'rejected'
        self.save()

class FollowNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='follow_notifications', on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.user.username}: {self.message}"