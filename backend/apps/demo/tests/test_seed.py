import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.accounts.models import User
from apps.careers.models import Application
from apps.community.models import Group
from apps.learning.models import Course
from apps.messaging.models import Message
from apps.notifications.models import Notification
from apps.payments.models import Order


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_seed_builds_a_demo_and_is_idempotent(django_capture_on_commit_callbacks, monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "chosen-for-this-test")
    with django_capture_on_commit_callbacks(execute=True):
        call_command("seed_demo")
    assert User.objects.filter(email__endswith="@demo.lms").count() == 7
    assert Course.objects.filter(status="published").count() == 3
    assert Group.objects.count() == 2 and Application.objects.count() == 2
    assert Message.objects.count() == 4
    assert Notification.objects.filter(recipient__username="lina").exists()
    assert User.objects.get(username="lina").check_password("chosen-for-this-test")

    call_command("seed_demo")
    assert User.objects.filter(email__endswith="@demo.lms").count() == 7, (
        "a second run does nothing"
    )
    paid = Course.objects.get(price_cents__gt=0)
    Order.objects.create(
        buyer=User.objects.get(username="omar"), course=paid, amount_cents=2900, currency="usd"
    )
    call_command("seed_demo", "--reset")
    assert User.objects.filter(email__endswith="@demo.lms").count() == 7, "reset rebuilds"


@pytest.mark.django_db
def test_seed_refuses_without_debug():
    with pytest.raises(CommandError):
        call_command("seed_demo")


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_seed_makes_up_a_password_when_none_is_given(monkeypatch, capsys):
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    call_command("seed_demo")
    password = capsys.readouterr().out.strip().rsplit(" ", 1)[-1]
    assert len(password) >= 12 and User.objects.get(username="lina").check_password(password)
