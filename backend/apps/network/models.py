from django.conf import settings
from django.db import models
from django.db.models.functions import Greatest, Least

from apps.core.models import TimeStampedModel


class Follow(TimeStampedModel):
    """One-way: `follower` sees `following`'s activity."""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following_set"
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follower_set"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="follow_once"),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("following")), name="follow_not_self"
            ),
        ]

    def __str__(self):
        return f"{self.follower_id} → {self.following_id}"


class Connection(TimeStampedModel):
    """Two-way, after the addressee accepts. One row per pair, whichever side asked."""

    class Status(models.TextChoices):
        PENDING = "pending"
        ACCEPTED = "accepted"

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="connections_sent"
    )
    addressee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="connections_received"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Least("requester", "addressee"),
                Greatest("requester", "addressee"),
                name="connection_pair_once",
            ),
            models.CheckConstraint(
                condition=~models.Q(requester=models.F("addressee")), name="connection_not_self"
            ),
        ]
        indexes = [models.Index(fields=["addressee", "status"], name="connection_inbox_idx")]

    def __str__(self):
        return f"{self.requester_id} ↔ {self.addressee_id} ({self.status})"

    def other(self, user):
        return self.addressee if self.requester_id == user.id else self.requester


class Recommendation(TimeStampedModel):
    """Written by a connection. Shows on the recipient's profile only once they publish it."""

    class Status(models.TextChoices):
        PENDING = "pending"
        PUBLISHED = "published"
        HIDDEN = "hidden"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendations_written"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendations"
    )
    relationship = models.CharField(max_length=160)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["author", "recipient"], name="recommendation_once"),
            models.CheckConstraint(
                condition=~models.Q(author=models.F("recipient")), name="recommendation_not_self"
            ),
        ]
        indexes = [models.Index(fields=["recipient", "status"], name="recommendation_profile_idx")]

    def __str__(self):
        return f"{self.author_id} recommends {self.recipient_id}"
