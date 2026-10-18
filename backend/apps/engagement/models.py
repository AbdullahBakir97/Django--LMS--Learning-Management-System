from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Comment(TimeStampedModel):
    """A comment on a registered target. Replies go one level deep."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    target_type = models.CharField(max_length=32)
    target_id = models.PositiveBigIntegerField()
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    body = models.TextField(max_length=5000)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["target_type", "target_id", "created_at"], name="comment_target_idx"
            )
        ]

    def __str__(self):
        return f"comment {self.pk} on {self.target_type}:{self.target_id}"


class Reaction(TimeStampedModel):
    class Kind(models.TextChoices):
        LIKE = "like", "Like"
        CELEBRATE = "celebrate", "Celebrate"
        INSIGHTFUL = "insightful", "Insightful"
        SUPPORT = "support", "Support"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reactions"
    )
    target_type = models.CharField(max_length=32)
    target_id = models.PositiveBigIntegerField()
    kind = models.CharField(max_length=16, choices=Kind.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_type", "target_id"], name="reaction_once_per_target"
            )
        ]
        indexes = [models.Index(fields=["target_type", "target_id"], name="reaction_target_idx")]

    def __str__(self):
        return f"{self.kind} on {self.target_type}:{self.target_id}"
