from django.db.models import Count, F, OuterRef, Prefetch, Q, Subquery

from apps.network.models import Connection

from .models import Conversation, Message, Participant


def connected(a, b) -> bool:
    return Connection.objects.filter(
        Q(requester=a, addressee=b) | Q(requester=b, addressee=a),
        status=Connection.Status.ACCEPTED,
    ).exists()


def participant(user, conversation_id) -> Participant | None:
    return (
        Participant.objects.filter(user=user, conversation_id=conversation_id)
        .select_related("conversation")
        .first()
    )


def participant_ids(conversation_id) -> list[int]:
    return list(
        Participant.objects.filter(conversation_id=conversation_id).values_list(
            "user_id", flat=True
        )
    )


def conversations_for(user):
    """Newest activity first, with your unread count and the last message."""
    mine = Participant.objects.filter(conversation=OuterRef("pk"), user=user)
    last = Message.objects.filter(conversation=OuterRef("pk")).order_by("-created_at")
    people = Participant.objects.select_related("user__profile")
    return (
        Conversation.objects.filter(participants__user=user)
        .annotate(
            my_last_read=Subquery(mine.values("last_read_at")[:1]),
            last_message_id=Subquery(last.values("id")[:1]),
        )
        .annotate(
            unread=Count(
                "messages",
                filter=Q(messages__deleted_at__isnull=True)
                & ~Q(messages__sender=user)
                & (Q(my_last_read__isnull=True) | Q(messages__created_at__gt=F("my_last_read"))),
            )
        )
        .prefetch_related(Prefetch("participants", queryset=people))
        .order_by(F("last_message_at").desc(nulls_last=True), "-created_at")
    )


def messages_in(conversation_id):
    return Message.objects.filter(conversation_id=conversation_id).select_related("sender__profile")


def unread_total(user) -> int:
    return sum(c.unread for c in conversations_for(user))
