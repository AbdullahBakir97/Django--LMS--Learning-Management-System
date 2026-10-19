from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Report(TimeStampedModel):
    """Someone flags a post, a comment or a person. Staff resolve every report on it at once."""

    class Kind(models.TextChoices):
        POST = "post", "Post"
        COMMENT = "comment", "Comment"
        USER = "user", "Person"

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam or scam"
        HARASSMENT = "harassment", "Harassment or bullying"
        HATE = "hate", "Hate or violence"
        MISINFORMATION = "misinformation", "False information"
        INAPPROPRIATE = "inappropriate", "Sexual or inappropriate"
        OTHER = "other", "Something else"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REMOVED = "removed", "Content removed"
        DISMISSED = "dismissed", "No action needed"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_made"
    )
    kind = models.CharField(max_length=8, choices=Kind.choices)
    object_id = models.PositiveBigIntegerField()
    reason = models.CharField(max_length=16, choices=Reason.choices)
    details = models.TextField(blank=True, max_length=1000)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["reporter", "kind", "object_id"], name="report_once_per_person"
            )
        ]
        indexes = [models.Index(fields=["status", "kind", "object_id"], name="report_queue_idx")]

    def __str__(self):
        return f"{self.kind}:{self.object_id} by {self.reporter_id} ({self.status})"
