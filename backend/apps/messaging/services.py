"""Writes with rules. Every function takes the acting user first.

Pushes go to every participant's WebSocket after commit, including the sender's other tabs.
"""

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core.realtime import publish_to_user

from .models import Conversation, Message, Participant
from .selectors import connected, participant_ids
from .serializers import MessageSerializer


def _push(conversation_id, event: str, data: dict, exclude: int | None = None) -> None:
    ids = [uid for uid in participant_ids(conversation_id) if uid != exclude]
    transaction.on_commit(lambda: [publish_to_user(uid, event, data) for uid in ids])


def start(actor, others: list, title: str = "") -> Conversation:
    """Talk to your connections: one person gives the direct conversation (reused if it exists)."""
    others = [u for u in dict.fromkeys(others) if u.id != actor.id]
    if not others:
        raise ValidationError({"usernames": "Choose someone other than yourself."})
    strangers = [u.username for u in others if not connected(actor, u)]
    if strangers:
        raise PermissionDenied(
            f"You can message your connections. Not connected: {', '.join(strangers)}."
        )
    if len(others) == 1:
        key = Conversation.key_for(actor.id, others[0].id)
        existing = Conversation.objects.filter(direct_key=key).first()
        if existing:
            return existing
        try:
            with transaction.atomic():
                conversation = Conversation.objects.create(direct_key=key)
                Participant.objects.bulk_create(
                    [Participant(conversation=conversation, user=u) for u in (actor, others[0])]
                )
        except IntegrityError:  # both people started it at the same moment
            return Conversation.objects.get(direct_key=key)
        return conversation
    with transaction.atomic():
        conversation = Conversation.objects.create(is_group=True, title=title.strip())
        Participant.objects.bulk_create(
            [Participant(conversation=conversation, user=u) for u in [actor, *others]]
        )
    return conversation


def _require_participant(actor, conversation_id) -> Participant:
    p = Participant.objects.filter(user=actor, conversation_id=conversation_id).first()
    if p is None:
        raise PermissionDenied()
    return p


@transaction.atomic
def send(actor, conversation: Conversation, body: str) -> Message:
    me = _require_participant(actor, conversation.id)
    if not body.strip():
        raise ValidationError({"body": "Write something first."})
    message = Message.objects.create(conversation=conversation, sender=actor, body=body.strip())
    Conversation.objects.filter(pk=conversation.pk).update(last_message_at=message.created_at)
    me.last_read_at = message.created_at
    me.save(update_fields=["last_read_at", "updated_at"])
    _push(conversation.id, "message.created", MessageSerializer(message).data)
    return message


def edit(actor, message: Message, body: str) -> Message:
    if message.sender_id != actor.id or message.deleted_at:
        raise PermissionDenied("Only the sender can edit a message.")
    message.body = body.strip()
    message.edited_at = timezone.now()
    message.save(update_fields=["body", "edited_at", "updated_at"])
    _push(message.conversation_id, "message.updated", MessageSerializer(message).data)
    return message


def delete(actor, message: Message) -> Message:
    if message.sender_id != actor.id:
        raise PermissionDenied("Only the sender can remove a message.")
    message.body = ""
    message.deleted_at = timezone.now()
    message.save(update_fields=["body", "deleted_at", "updated_at"])
    _push(message.conversation_id, "message.updated", MessageSerializer(message).data)
    return message


def mark_read(actor, conversation: Conversation) -> None:
    p = _require_participant(actor, conversation.id)
    p.last_read_at = timezone.now()
    p.save(update_fields=["last_read_at", "updated_at"])
    _push(
        conversation.id,
        "conversation.read",
        {
            "conversation": conversation.id,
            "username": actor.username,
            "at": p.last_read_at.isoformat(),
        },
    )


def typing(actor, conversation_id) -> None:
    """Called from the WebSocket: tell the others someone is writing. Nothing is stored."""
    if not Participant.objects.filter(user=actor, conversation_id=conversation_id).exists():
        return
    data = {
        "conversation": conversation_id,
        "username": actor.username,
        "name": actor.get_full_name() or actor.username,
    }
    for uid in participant_ids(conversation_id):
        if uid != actor.id:
            publish_to_user(uid, "conversation.typing", data)
