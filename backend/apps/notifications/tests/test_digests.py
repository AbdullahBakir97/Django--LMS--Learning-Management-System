import re
from datetime import UTC, datetime, time
from pathlib import Path
from unittest import mock

import pytest
from django.conf import settings

from apps.notifications import schedule
from apps.notifications.models import Notification, Preference
from apps.notifications.services import notify
from apps.notifications.tasks import send_digests

Kind = Notification.Kind


def at(*args):
    return datetime(*args, tzinfo=UTC)


def pref(**fields):
    return Preference(**{"timezone": "UTC", "digest": "off", **fields})


def test_quiet_hours_across_midnight_in_the_readers_zone():
    p = pref(quiet_start=time(22), quiet_end=time(7), timezone="Asia/Amman")  # UTC+3
    assert schedule.quiet_until(p, at(2026, 10, 18, 12)) is None  # 15:00 there
    until = schedule.quiet_until(p, at(2026, 10, 18, 20))  # 23:00 there
    assert until.astimezone(UTC) == at(2026, 10, 19, 4)  # 07:00 there
    assert schedule.quiet_until(p, at(2026, 10, 19, 1)).astimezone(UTC) == at(2026, 10, 19, 4)
    assert (
        schedule.quiet_until(pref(quiet_start=time(9), quiet_end=time(9)), at(2026, 1, 1, 9))
        is None
    )


def test_digest_is_due_at_eight_local_once():
    daily = pref(digest="daily", timezone="America/New_York")  # UTC-4 in October
    assert schedule.digest_due(daily, at(2026, 10, 18, 12))  # 08:00 there
    assert not schedule.digest_due(daily, at(2026, 10, 18, 13))
    daily.last_digest_at = at(2026, 10, 18, 12)
    assert not schedule.digest_due(daily, at(2026, 10, 18, 12, 30))
    weekly = pref(digest="weekly")
    assert schedule.digest_due(weekly, at(2026, 10, 19, 8))  # a Monday
    assert not schedule.digest_due(weekly, at(2026, 10, 20, 8))
    assert not schedule.digest_due(pref(), at(2026, 10, 19, 8))


@pytest.mark.django_db
def test_digest_replaces_instant_email_and_lists_unread(
    user, mailoutbox, django_capture_on_commit_callbacks
):
    Preference.objects.create(user=user, digest="daily", muted_kinds=["follow"])
    with django_capture_on_commit_callbacks(execute=True):
        notify(user.id, Kind.COURSE_COMPLETED, "You completed SQL", url="/c/1")
    assert mailoutbox == [], "no instant email when a digest is chosen"
    notify(user.id, Kind.ENROLMENT, "Sami enrolled")
    read = notify(user.id, Kind.ENROLMENT, "Already seen")
    read.read_at = read.created_at
    read.save()

    eight = datetime.now(UTC).replace(hour=8, minute=0)
    with mock.patch("django.utils.timezone.now", return_value=eight):
        assert send_digests() == 1
        assert send_digests() == 0, "not twice in one day"
    (mail,) = mailoutbox
    assert "daily digest: 2 new" in mail.subject
    assert "You completed SQL" in mail.body and "Sami enrolled" in mail.body
    assert "Already seen" not in mail.body and f"{settings.FRONTEND_URL}/c/1" in mail.body


@pytest.mark.django_db
def test_quiet_hours_delay_instant_email(user, django_capture_on_commit_callbacks):
    Preference.objects.create(user=user, quiet_start=time(22), quiet_end=time(7))
    night = at(2026, 10, 18, 3)
    with (
        mock.patch("django.utils.timezone.now", return_value=night),
        mock.patch("apps.notifications.services.send_notification_email") as task,
        django_capture_on_commit_callbacks(execute=True),
    ):
        notify(user.id, Kind.COURSE_COMPLETED, "You completed SQL")
    assert task.apply_async.call_args.kwargs["eta"].astimezone(UTC) == at(2026, 10, 18, 7)


@pytest.mark.django_db
def test_preference_validation(auth_client):
    url = "/api/notifications/preferences/"
    ok = auth_client.patch(
        url,
        {
            "digest": "weekly",
            "quiet_start": "22:00",
            "quiet_end": "07:00",
            "timezone": "Africa/Lagos",
        },
        format="json",
    )
    assert ok.status_code == 200 and ok.data["digest"] == "weekly"
    assert auth_client.patch(url, {"timezone": "Mars/Base"}, format="json").status_code == 400
    assert auth_client.patch(url, {"quiet_end": None}, format="json").status_code == 400


FRONTEND = Path(settings.BASE_DIR).parent / "frontend/src"


@pytest.mark.skipif(not FRONTEND.exists(), reason="needs the whole repository")
def test_every_kind_has_an_icon_in_the_app():
    """A kind the frontend does not know renders without an icon; keep the two in step."""
    root = FRONTEND
    declared = set(re.findall(r"\| '(\w+)'", (root / "api/notifications.ts").read_text()))
    icons = set(
        re.findall(r"^  (\w+): Ph", (root / "features/notifications/format.ts").read_text(), re.M)
    )
    assert set(Kind.values) <= declared and set(Kind.values) <= icons


@pytest.mark.django_db
def test_a_held_email_is_dropped_if_read_or_switched_off_meanwhile(user, mailoutbox):
    from apps.notifications.tasks import send_notification_email

    seen = notify(user.id, Kind.COURSE_COMPLETED, "Seen in the app")
    seen.read_at = seen.created_at
    seen.save()
    send_notification_email(seen.id)
    muted = notify(user.id, Kind.COURSE_COMPLETED, "Email turned off later")
    Preference.objects.create(user=user, email_enabled=False)
    send_notification_email(muted.id)
    assert mailoutbox == []


@pytest.mark.django_db
def test_one_failing_digest_does_not_stop_the_others(mailoutbox):
    from conftest import UserFactory

    readers = UserFactory.create_batch(3)
    for u in readers:
        Preference.objects.create(user=u, digest="daily")
        notify(u.id, Kind.ENROLMENT, f"For {u.username}")
    real = __import__("django.core.mail", fromlist=["send_mail"]).send_mail
    calls = []

    def flaky(subject, body, sender, to):
        calls.append(to)
        if len(calls) == 1:
            raise OSError("SMTP down")
        return real(subject, body, sender, to)

    eight = datetime.now(UTC).replace(hour=8, minute=0)
    with (
        mock.patch("django.utils.timezone.now", return_value=eight),
        mock.patch("apps.notifications.tasks.send_mail", flaky),
    ):
        assert send_digests() == 2
        failed = Preference.objects.get(user__email=calls[0][0])
        assert failed.last_digest_at is None, "retried by a re-run"
        assert send_digests() == 1
    assert len(mailoutbox) == 3
