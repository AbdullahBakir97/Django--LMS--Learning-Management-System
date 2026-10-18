from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Conversation(TimeStampedModel):
    """A direct conversation between two people, or a small group thread."""

    title = models.CharField(max_length=120, blank=True)
    is_group = models.BooleanField(default=False)
    # "min:max" of the two user ids for direct conversations, so a pair has exactly one.
    direct_key = models.CharField(max_length=41, unique=True, null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)

    def __str__(self):
        return self.title or f"conversation {self.pk}"

    @staticmethod
    def key_for(a_id: int, b_id: int) -> str:
        low, high = sorted((a_id, b_id))
        return f"{low}:{high}"


class Participant(TimeStampedModel):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversation_memberships"
    )
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["conversation", "user"], name="participant_once")
        ]


class Message(TimeStampedModel):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="messages_sent"
    )
    body = models.TextField(max_length=4000)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["conversation", "-created_at"], name="message_conversation_idx")
        ]

    def __str__(self):
        return f"message {self.pk} in {self.conversation_id}"
