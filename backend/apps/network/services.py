"""Writes with rules. Every function takes the acting user first."""

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core import events

from . import events as names
from .models import Connection, Follow, Recommendation
from .selectors import connection_between, connections_of_id


def _name(user) -> str:
    return user.get_full_name() or user.username


def follow(actor, other) -> Follow:
    if actor.id == other.id:
        raise ValidationError("You cannot follow yourself.")
    record, created = Follow.objects.get_or_create(follower=actor, following=other)
    if created:
        events.publish(
            names.FOLLOWED,
            follower_id=actor.id,
            follower_name=_name(actor),
            follower_username=actor.username,
            following_id=other.id,
        )
    return record


def unfollow(actor, other) -> None:
    Follow.objects.filter(follower=actor, following=other).delete()


def request_connection(actor, other) -> Connection:
    """Ask to connect. If they already asked you, this accepts their request instead."""
    if actor.id == other.id:
        raise ValidationError("You cannot connect with yourself.")
    existing = connection_between(actor, other)
    if existing:
        if existing.status == Connection.Status.PENDING and existing.addressee_id == actor.id:
            return accept(actor, existing)
        raise ValidationError("You are already connected or have a pending request.")
    try:
        with transaction.atomic():
            connection = Connection.objects.create(requester=actor, addressee=other)
    except IntegrityError:  # the other side asked at the same moment
        raise ValidationError("You are already connected or have a pending request.") from None
    events.publish(
        names.CONNECTION_REQUESTED,
        connection_id=connection.id,
        requester_id=actor.id,
        requester_name=_name(actor),
        addressee_id=other.id,
    )
    return connection


def accept(actor, connection: Connection) -> Connection:
    if connection.addressee_id != actor.id:
        raise PermissionDenied("Only the person asked can accept.")
    if connection.status == Connection.Status.ACCEPTED:
        return connection
    connection.status = Connection.Status.ACCEPTED
    connection.accepted_at = timezone.now()
    connection.save(update_fields=["status", "accepted_at", "updated_at"])
    events.publish(
        names.CONNECTION_ACCEPTED,
        connection_id=connection.id,
        requester_id=connection.requester_id,
        addressee_id=actor.id,
        addressee_name=_name(actor),
        addressee_username=actor.username,
        connection_counts={
            uid: connections_of_id(uid).count() for uid in (connection.requester_id, actor.id)
        },
    )
    return connection


def decline(actor, connection: Connection) -> None:
    """The addressee says no. The row goes, so either side may ask again later."""
    if connection.addressee_id != actor.id or connection.status != Connection.Status.PENDING:
        raise PermissionDenied("Only the person asked can decline a pending request.")
    connection.delete()


def remove(actor, connection: Connection) -> None:
    """Withdraw your request, or end a connection. Either side may do it."""
    if actor.id not in (connection.requester_id, connection.addressee_id):
        raise PermissionDenied()
    connection.delete()


def _require_connection(actor, other, message: str) -> None:
    connection = connection_between(actor, other)
    if connection is None or connection.status != Connection.Status.ACCEPTED:
        raise PermissionDenied(message)


def request_recommendation(actor, other, message: str = "") -> None:
    # shortcut: no stored request, so asking twice notifies twice; add a model if that gets abused
    _require_connection(actor, other, "You can only ask your connections.")
    events.publish(
        names.RECOMMENDATION_REQUESTED,
        requester_id=actor.id,
        requester_name=_name(actor),
        requester_username=actor.username,
        recipient_id=other.id,
        message=message,
    )


def write_recommendation(actor, other, relationship: str, body: str) -> Recommendation:
    """Write or rewrite. A rewrite goes back to pending: the recipient approves what shows."""
    if actor.id == other.id:
        raise ValidationError("You cannot recommend yourself.")
    _require_connection(actor, other, "You can only recommend your connections.")
    recommendation, _ = Recommendation.objects.update_or_create(
        author=actor,
        recipient=other,
        defaults={
            "relationship": relationship,
            "body": body,
            "status": Recommendation.Status.PENDING,
        },
    )
    events.publish(
        names.RECOMMENDATION_WRITTEN,
        author_id=actor.id,
        author_name=_name(actor),
        recipient_id=other.id,
    )
    return recommendation


def set_recommendation_status(actor, recommendation: Recommendation, status: str):
    if recommendation.recipient_id != actor.id:
        raise PermissionDenied("Only the person recommended decides what shows.")
    if status == Recommendation.Status.PENDING:
        raise ValidationError({"status": "Choose published or hidden."})
    was = recommendation.status
    recommendation.status = status
    recommendation.save(update_fields=["status", "updated_at"])
    if status == Recommendation.Status.PUBLISHED and was != status:
        events.publish(
            names.RECOMMENDATION_PUBLISHED,
            recipient_id=actor.id,
            author_id=recommendation.author_id,
            recipient_name=_name(actor),
            recipient_username=actor.username,
        )
    return recommendation


def delete_recommendation(actor, recommendation: Recommendation) -> None:
    if actor.id not in (recommendation.author_id, recommendation.recipient_id):
        raise PermissionDenied("This is not your recommendation.")
    recommendation.delete()
