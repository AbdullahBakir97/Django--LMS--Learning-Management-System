from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import Notification


@shared_task
def send_notification_email(notification_id: int) -> None:
    n = Notification.objects.select_related("recipient").filter(pk=notification_id).first()
    if n is None:
        return
    link = f"{settings.FRONTEND_URL}{n.url}" if n.url else settings.FRONTEND_URL
    body = "\n\n".join(part for part in (n.body, link) if part)
    send_mail(f"[LMS] {n.title}", body, None, [n.recipient.email])
