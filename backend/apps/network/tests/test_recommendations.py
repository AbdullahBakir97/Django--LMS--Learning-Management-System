import pytest
from rest_framework.test import APIClient

from apps.network.models import Connection
from apps.notifications.models import Notification
from apps.profiles.models import Achievement
from conftest import UserFactory

BODY = "Nour led our data team for two years and shipped every release on time."


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture
def run_events(django_capture_on_commit_callbacks):
    return lambda: django_capture_on_commit_callbacks(execute=True)


@pytest.fixture
def pair(user):
    nour = UserFactory(username="nour")
    Connection.objects.create(requester=user, addressee=nour, status="accepted")
    return user, nour


@pytest.mark.django_db
def test_only_connections_can_ask_or_write(user, auth_client):
    UserFactory(username="stranger")
    url = "/api/network/stranger/recommendations/"
    payload = {"relationship": "Worked together", "body": BODY}
    assert auth_client.post(url, payload).status_code == 403
    assert auth_client.post(url + "request/", {}).status_code == 403
    assert (
        auth_client.post(f"/api/network/{user.username}/recommendations/", payload).status_code
        == 400
    )


@pytest.mark.django_db
def test_recommendation_flow(pair, auth_client, run_events):
    user, nour = pair
    nour_client = client_for(nour)

    with run_events():
        assert (
            nour_client.post(
                f"/api/network/{user.username}/recommendations/request/", {"message": "Could you?"}
            ).status_code
            == 202
        )
    assert Notification.objects.filter(recipient=user, kind="recommendation_request").exists()

    url = "/api/network/nour/recommendations/"
    assert (
        auth_client.post(url, {"relationship": "Manager", "body": "Too short"}).status_code == 400
    )
    with run_events():
        written = auth_client.post(url, {"relationship": "I managed Nour at Acme", "body": BODY})
    assert written.status_code == 201, written.data
    assert written.data["status"] == "pending"
    assert Notification.objects.filter(recipient=nour, kind="recommendation").exists()

    # Pending ones are visible only to the person recommended.
    assert client_for(UserFactory()).get(url).data == []
    assert [r["status"] for r in nour_client.get(url).data] == ["pending"]

    rid = written.data["id"]
    assert (
        auth_client.patch(f"/api/recommendations/{rid}/", {"status": "published"}).status_code
        == 403
    )
    with run_events():
        published = nour_client.patch(f"/api/recommendations/{rid}/", {"status": "published"})
    assert published.data["status"] == "published"
    assert Achievement.objects.filter(user=nour, code="recommended").exists()
    assert len(client_for(UserFactory()).get(url).data) == 1

    # A rewrite goes back to pending; it stays one row.
    rewrite = auth_client.post(url, {"relationship": "Manager", "body": BODY + " Again."})
    assert rewrite.data["id"] == rid and rewrite.data["status"] == "pending"

    assert client_for(UserFactory()).delete(f"/api/recommendations/{rid}/").status_code == 404
    assert auth_client.delete(f"/api/recommendations/{rid}/").status_code == 204
