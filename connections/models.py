from django.db import models
from profiles.models import UserProfile

class ConnectionRequest(models.Model):
    from_user = models.ForeignKey(UserProfile, related_name='connection_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(UserProfile, related_name='connection_requests_received', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.from_user} wants to connect with {self.to_user}"

    def accept(self):
        self.status = 'accepted'
        Connection.objects.create(user=self.to_user, connection=self.from_user)
        self.save()

    def reject(self):
        self.status = 'rejected'
        self.save()

class Connection(models.Model):
    user = models.ForeignKey(UserProfile, related_name='connections', on_delete=models.CASCADE)
    connection = models.ForeignKey(UserProfile, related_name='connected_users', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} is connected with {self.connection}"

class Recommendation(models.Model):
    recommended_by = models.ForeignKey(UserProfile, related_name='recommendations_given', on_delete=models.CASCADE)
    recommended_user = models.ForeignKey(UserProfile, related_name='recommendations_received', on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return f"{self.recommended_by} recommended {self.recommended_user}"