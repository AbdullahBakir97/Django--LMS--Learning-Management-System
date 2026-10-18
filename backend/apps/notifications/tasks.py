import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from . import schedule
from .models import Notification, Preference

logger = logging.getLogger(__name__)


@shared_task
def send_notification_email(notification_id: int) -> None:
    n = Notification.objects.select_related("recipient").filter(pk=notification_id).first()
    if n is None or n.read_at:
        return  # gone, or already read in the app while quiet hours held the email
    # Settings may have changed while the email waited.
    preference = Preference.objects.filter(user_id=n.recipient_id).first()
    if preference and (
        not preference.email_enabled
        or n.kind in preference.muted_kinds
        or preference.digest != Preference.Digest.OFF
    ):
        return
    link = f"{settings.FRONTEND_URL}{n.url}" if n.url else settings.FRONTEND_URL
    body = "\n\n".join(part for part in (n.body, link) if part)
    send_mail(f"[LMS] {n.title}", body, None, [n.recipient.email])


DIGEST_LIMIT = 20


@shared_task
def send_digests() -> int:
    """Hourly. One email per reader whose digest is due, listing what they have not read."""
    now = timezone.now()
    sent = 0
    due = Preference.objects.filter(email_enabled=True).exclude(digest=Preference.Digest.OFF)
    for preference in due.select_related("user"):
        if not schedule.digest_due(preference, now):
            continue
        items = list(
            Notification.objects.filter(
                recipient=preference.user,
                read_at__isnull=True,
                created_at__gt=schedule.digest_window(preference, now),
            )
            .exclude(kind__in=preference.muted_kinds)
            .order_by("-created_at")[:DIGEST_LIMIT]
        )
        if items:
            try:
                _send_digest(preference, items)
            except Exception:  # one bad address or SMTP hiccup must not stop everyone else's
                logger.exception("digest failed", extra={"user": preference.user_id})
                continue  # not marked sent, so a re-run of this hour retries it
            sent += 1
        preference.last_digest_at = now
        preference.save(update_fields=["last_digest_at", "updated_at"])
    return sent


def _send_digest(preference, items) -> None:
    period = "week" if preference.digest == Preference.Digest.WEEKLY else "day"
    lines = [f"What happened this {period} that you have not seen yet:", ""]
    for n in items:
        lines.append(f"- {n.title}")
        if n.url:
            lines.append(f"  {settings.FRONTEND_URL}{n.url}")
    lines += ["", f"All notifications: {settings.FRONTEND_URL}/notifications"]
    subject = f"[LMS] Your {'weekly' if period == 'week' else 'daily'} digest: {len(items)} new"
    send_mail(subject, "\n".join(lines), None, [preference.user.email])
