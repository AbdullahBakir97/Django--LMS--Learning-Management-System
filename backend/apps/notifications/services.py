"""The one write path for notifications: store, push live, and email the kinds that warrant it."""

from django.db import transaction
from django.utils import timezone

from apps.core.realtime import publish_to_user

from .models import Notification, Preference
from .serializers import NotificationSerializer
from .tasks import send_notification_email

EMAIL_KINDS = {
    Notification.Kind.COURSE_COMPLETED,
    Notification.Kind.APPLICATION_UPDATE,
    Notification.Kind.INTERVIEW,
}


def notify(recipient_id, kind, title, *, body="", url="", actor_id=None) -> Notification | None:
    if recipient_id == actor_id:
        return None
    preference = Preference.objects.filter(user_id=recipient_id).first()
    if preference and kind in preference.muted_kinds:
        return None
    notification = Notification.objects.create(
        recipient_id=recipient_id, actor_id=actor_id, kind=kind, title=title, body=body, url=url
    )
    payload = NotificationSerializer(notification).data
    transaction.on_commit(lambda: publish_to_user(recipient_id, "notification.created", payload))
    if kind in EMAIL_KINDS and (preference is None or preference.email_enabled):
        transaction.on_commit(lambda: send_notification_email.delay(notification.id))
    return notification


def mark_read(actor, notification: Notification) -> Notification:
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at", "updated_at"])
        transaction.on_commit(
            lambda: publish_to_user(actor.id, "notification.read", {"ids": [notification.id]})
        )
    return notification


def mark_all_read(actor) -> int:
    count = Notification.objects.filter(recipient=actor, read_at__isnull=True).update(
        read_at=timezone.now()
    )
    if count:
        transaction.on_commit(lambda: publish_to_user(actor.id, "notification.read", {"all": True}))
    return count
