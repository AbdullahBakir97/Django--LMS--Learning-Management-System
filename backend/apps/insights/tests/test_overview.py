from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.learning.models import Enrollment
from apps.learning.tests.test_learning import CourseFactory
from apps.moderation.models import Report
from apps.payments.models import Order
from conftest import UserFactory


@pytest.fixture
def admin_client(db):
    c = APIClient()
    c.force_authenticate(UserFactory(role="admin"))
    return c


@pytest.mark.django_db
def test_only_admins_see_the_overview(auth_client, api_client):
    assert api_client.get("/api/insights/overview/").status_code == 401
    assert auth_client.get("/api/insights/overview/").status_code == 403


@pytest.mark.django_db
def test_overview_counts(admin_client):
    popular, quiet = CourseFactory(title="Popular"), CourseFactory(title="Quiet")
    CourseFactory(status="draft")
    learners = UserFactory.create_batch(3)
    for u in learners:
        Enrollment.objects.create(course=popular, student=u)
    old = Enrollment.objects.create(course=quiet, student=learners[0], status="completed")
    Enrollment.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=60))
    UserFactory(is_active=False)

    for reporter in learners[:2]:  # two reports on one person: one item to review
        Report.objects.create(reporter=reporter, kind="user", object_id=99, reason="spam")
    now = timezone.now()
    for amount, currency, paid_at in [(2900, "usd", now), (2900, "usd", now - timedelta(days=40))]:
        Order.objects.create(
            buyer=learners[1],
            course=popular,
            amount_cents=amount,
            paid_cents=amount,
            currency=currency,
            status="paid",
            paid_at=paid_at,
        )
    Order.objects.create(buyer=learners[2], course=popular, amount_cents=2900, currency="usd")

    data = admin_client.get("/api/insights/overview/").json()
    # 3 learners, 3 instructors from the factory, the admin; the deactivated one is left out.
    assert data["people"] == 7
    assert data["courses"] == 2
    assert (data["enrolments"], data["new_enrolments"], data["completion_rate"]) == (4, 3, 25)
    assert data["open_reports"] == 1
    assert data["revenue"] == [
        {"currency": "usd", "total_cents": 5800, "recent_cents": 2900, "orders": 2}
    ]
    assert [c["title"] for c in data["top_courses"]] == ["Popular", "Quiet"]
    assert data["top_courses"][0]["new_enrolments"] == 3
    assert len(data["weekly_signups"]) == 12 and data["weekly_enrolments"][-1]["count"] == 3
