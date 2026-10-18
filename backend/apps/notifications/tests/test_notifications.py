import json

import pytest
from asgiref.sync import async_to_sync
from asgiref.testing import ApplicationCommunicator
from channels.layers import get_channel_layer
from django.core import signing
from rest_framework.test import APIClient

from apps.core.realtime import TICKET_SALT, user_group
from apps.notifications.models import Notification, Preference
from apps.notifications.services import notify
from apps.profiles.models import ProfileSkill, Skill
from config.asgi import application
from conftest import UserFactory


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture
def run_events(django_capture_on_commit_callbacks):
    """Run on-commit callbacks (events, pushes, mail) inside the test transaction."""
    return lambda: django_capture_on_commit_callbacks(execute=True)


@pytest.mark.django_db
def test_enrolment_notifies_the_instructor(run_events):
    from apps.learning.models import Course, Lesson

    instructor = UserFactory(role="instructor")
    student = UserFactory(first_name="Lina", last_name="Haddad")
    course = Course.objects.create(instructor=instructor, title="Intro to SQL", status="published")
    Lesson.objects.create(course=course, title="One", order=1)

    with run_events():
        assert client_for(student).post(f"/api/courses/{course.slug}/enroll/").status_code == 201

    n = Notification.objects.get(recipient=instructor)
    assert n.kind == Notification.Kind.ENROLMENT
    assert n.title == "Lina Haddad enrolled in Intro to SQL"
    assert n.url == f"/teach/{course.slug}" and n.actor == student


@pytest.mark.django_db
def test_endorsement_notifies_once(run_events, user, auth_client):
    owner = UserFactory()
    skill = ProfileSkill.objects.create(
        profile=owner.profile, skill=Skill.objects.create(name="Django")
    )
    url = f"/api/profiles/{owner.username}/skills/{skill.id}/endorse/"
    with run_events():
        auth_client.post(url)
        auth_client.post(url)
    assert Notification.objects.filter(recipient=owner, kind="endorsement").count() == 1


@pytest.mark.django_db
def test_course_completion_is_emailed_unless_disabled(run_events, user, mailoutbox):
    with run_events():
        notify(user.id, Notification.Kind.COURSE_COMPLETED, "You completed SQL", url="/c/1")
    assert len(mailoutbox) == 1 and mailoutbox[0].to == [user.email]
    assert mailoutbox[0].body.endswith("/c/1")

    Preference.objects.create(user=user, email_enabled=False)
    with run_events():
        notify(user.id, Notification.Kind.COURSE_COMPLETED, "You completed Go")
    assert len(mailoutbox) == 1
    assert Notification.objects.filter(recipient=user).count() == 2


@pytest.mark.django_db
def test_muted_kinds_and_self_actions_are_skipped(user):
    Preference.objects.create(user=user, muted_kinds=["endorsement"])
    assert notify(user.id, Notification.Kind.ENDORSEMENT, "x", actor_id=None) is None
    assert notify(user.id, Notification.Kind.ENROLMENT, "x", actor_id=user.id) is None
    assert notify(user.id, Notification.Kind.ENROLMENT, "x") is not None


@pytest.mark.django_db
def test_list_read_and_delete_are_owner_only(user, auth_client):
    mine = [notify(user.id, Notification.Kind.ENROLMENT, f"n{i}") for i in range(3)]
    theirs = notify(UserFactory().id, Notification.Kind.ENROLMENT, "secret")

    data = auth_client.get("/api/notifications/").data
    assert [r["title"] for r in data["results"]] == ["n2", "n1", "n0"]
    assert auth_client.get("/api/notifications/unread-count/").data == {"count": 3}

    assert auth_client.post(f"/api/notifications/{theirs.id}/read/").status_code == 404
    assert auth_client.delete(f"/api/notifications/{theirs.id}/").status_code == 404

    assert auth_client.post(f"/api/notifications/{mine[0].id}/read/").data["read"] is True
    unread = auth_client.get("/api/notifications/?unread=true").data["results"]
    assert {r["id"] for r in unread} == {mine[1].id, mine[2].id}

    assert auth_client.post("/api/notifications/read-all/").data == {"count": 2}
    assert auth_client.get("/api/notifications/unread-count/").data == {"count": 0}
    assert auth_client.delete(f"/api/notifications/{mine[0].id}/").status_code == 204
    assert APIClient().get("/api/notifications/").status_code == 401


@pytest.mark.django_db
def test_preferences(auth_client):
    data = auth_client.get("/api/notifications/preferences/").data
    assert data["email_enabled"] is True and data["muted_kinds"] == []
    assert {k["value"] for k in data["kinds"]} == set(Notification.Kind.values)

    response = auth_client.patch(
        "/api/notifications/preferences/",
        {"email_enabled": False, "muted_kinds": ["endorsement", "endorsement"]},
        format="json",
    )
    assert response.data["email_enabled"] is False and response.data["muted_kinds"] == [
        "endorsement"
    ]
    bad = auth_client.patch(
        "/api/notifications/preferences/", {"muted_kinds": ["nope"]}, format="json"
    )
    assert bad.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_websocket_needs_a_valid_ticket_and_receives_pushes(user, auth_client):
    ticket = auth_client.post("/api/realtime/ticket/").data["ticket"]
    forged = signing.dumps(user.pk, salt="something-else")
    assert signing.loads(ticket, salt=TICKET_SALT) == user.pk

    async def connect(query: str):
        scope = {
            "type": "websocket",
            "path": "/ws/events/",
            "query_string": query.encode(),
            "headers": [(b"host", b"localhost"), (b"origin", b"http://localhost")],
            "subprotocols": [],
        }
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "websocket.connect"})
        return communicator, await communicator.receive_output(timeout=3)

    async def scenario():
        for query in ("", f"ticket={forged}", "ticket=garbage"):
            _, reply = await connect(query)
            assert reply == {"type": "websocket.close", "code": 4401}

        communicator, reply = await connect(f"ticket={ticket}")
        assert reply["type"] == "websocket.accept"
        await get_channel_layer().group_send(
            user_group(user.id),
            {"type": "push.event", "event": "notification.created", "data": {"id": 1}},
        )
        message = await communicator.receive_output(timeout=3)
        assert json.loads(message["text"]) == {"event": "notification.created", "data": {"id": 1}}
        await communicator.send_input({"type": "websocket.disconnect", "code": 1000})
        await communicator.wait(timeout=3)

    async_to_sync(scenario)()
