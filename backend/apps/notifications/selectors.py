from .models import Notification, Preference


def notifications_for(user, unread: bool | None = None):
    qs = Notification.objects.filter(recipient=user).select_related("actor")
    if unread is not None:
        qs = qs.filter(read_at__isnull=unread)
    return qs


def unread_count(user) -> int:
    return Notification.objects.filter(recipient=user, read_at__isnull=True).count()


def preference_for(user) -> Preference:
    return Preference.objects.get_or_create(user=user)[0]
