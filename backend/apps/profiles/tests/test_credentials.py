import pytest
from rest_framework.test import APIClient

from apps.core import events
from apps.network import services as network
from apps.network.models import Connection
from apps.notifications.models import Notification
from apps.profiles.models import Achievement
from conftest import UserFactory


@pytest.fixture
def run_events(django_capture_on_commit_callbacks):
    return lambda: django_capture_on_commit_callbacks(execute=True)


def codes(user):
    return set(Achievement.objects.filter(user=user).values_list("code", flat=True))


@pytest.mark.django_db
def test_portfolio_crud_shows_on_the_public_profile(auth_client, user):
    payload = {"title": "Open data portal", "url": "https://example.org", "completed_on": None}
    response = auth_client.post("/api/profiles/me/portfolio/", payload, format="json")
    assert response.status_code == 201, response.data
    item_id = response.data["id"]

    other = APIClient()
    other.force_authenticate(UserFactory())
    assert other.delete(f"/api/profiles/me/portfolio/{item_id}/").status_code == 404
    public = other.get(f"/api/profiles/{user.username}/").data
    assert [p["title"] for p in public["portfolio"]] == ["Open data portal"]
    assert public["achievements"] == []

    assert auth_client.delete(f"/api/profiles/me/portfolio/{item_id}/").status_code == 204


@pytest.mark.django_db
def test_course_events_award_badges_once_and_notify(user, run_events):
    with run_events():
        events.publish(
            "learning.course_completed",
            student_id=user.id,
            course_title="A",
            certificate_code="x",
            completed_count=1,
        )
    with run_events():
        events.publish(
            "learning.course_completed",
            student_id=user.id,
            course_title="B",
            certificate_code="y",
            completed_count=5,
        )
    with run_events():
        events.publish("learning.course_published", course_id=1, instructor_id=user.id)
    assert codes(user) == {"first_course", "five_courses", "first_published"}
    assert Notification.objects.filter(recipient=user, kind="achievement").count() == 3


@pytest.mark.django_db
def test_tenth_connection_earns_a_badge(user, run_events):
    for _ in range(9):
        Connection.objects.create(requester=user, addressee=UserFactory(), status="accepted")
    newcomer = UserFactory()
    pending = Connection.objects.create(requester=user, addressee=newcomer)
    with run_events():
        network.accept(newcomer, pending)
    assert "ten_connections" in codes(user)
    assert "ten_connections" not in codes(newcomer)


@pytest.mark.django_db
def test_first_endorsement_badge(user, auth_client, run_events):
    skill_id = auth_client.post("/api/profiles/me/skills/", {"name": "Django"}).data["id"]
    colleague = APIClient()
    colleague.force_authenticate(UserFactory())
    with run_events():
        response = colleague.post(f"/api/profiles/{user.username}/skills/{skill_id}/endorse/")
    assert response.status_code == 201
    assert codes(user) == {"first_endorsement"}
