from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    """One row per recipient. `url` is a path inside the SPA."""

    class Kind(models.TextChoices):
        ENROLMENT = "enrolment", "New enrolment in your course"
        COURSE_COMPLETED = "course_completed", "Course completed"
        ENDORSEMENT = "endorsement", "Skill endorsed"
        FOLLOW = "follow", "New follower"
        CONNECTION_REQUEST = "connection_request", "Connection request"
        CONNECTION_ACCEPTED = "connection_accepted", "Connection accepted"
        COMMENT = "comment", "Comment on your lesson"
        REPLY = "reply", "Reply to your comment"
        GROUP_REQUEST = "group_request", "Request to join your group"
        GROUP_APPROVED = "group_approved", "Group request approved"
        EVENT_RSVP = "event_rsvp", "Someone is going to your event"
        APPLICATION_RECEIVED = "application_received", "New application to your job"
        APPLICATION_UPDATE = "application_update", "Your application changed status"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    url = models.CharField(max_length=300, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "read_at"], name="notif_recipient_read_idx")]

    def __str__(self):
        return f"{self.kind} → {self.recipient_id}"


class Preference(TimeStampedModel):
    """Absent row means the defaults: email on, nothing muted."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preference"
    )
    email_enabled = models.BooleanField(default=True)
    muted_kinds = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"preferences for {self.user_id}"
