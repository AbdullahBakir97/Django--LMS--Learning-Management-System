"""Writes with rules. Every function takes the acting user first."""

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core import events

from . import events as names
from .models import Connection, Follow
from .selectors import connection_between


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
