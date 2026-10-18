import pytest
from django.db import IntegrityError
from rest_framework.test import APIClient

from apps.network.models import Connection, Follow
from apps.notifications.models import Notification
from apps.profiles.models import ProfileSkill, Skill
from conftest import UserFactory


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture
def run_events(django_capture_on_commit_callbacks):
    return lambda: django_capture_on_commit_callbacks(execute=True)


@pytest.mark.django_db
def test_follow_and_unfollow(user, auth_client, run_events):
    other = UserFactory(username="sami")
    with run_events():
        data = auth_client.post("/api/network/sami/follow/").data
        auth_client.post("/api/network/sami/follow/")
    assert data["following"] is True and data["followers"] == 1
    assert Notification.objects.filter(recipient=other, kind="follow").count() == 1

    followers = client_for(other).get("/api/network/sami/followers/").data["results"]
    assert [f["person"]["username"] for f in followers] == [user.username]
    following = auth_client.get(f"/api/network/{user.username}/following/").data["results"]
    assert [f["person"]["username"] for f in following] == ["sami"]

    assert auth_client.delete("/api/network/sami/follow/").data["following"] is False
    assert auth_client.post(f"/api/network/{user.username}/follow/").status_code == 400
    assert auth_client.get("/api/network/nobody/").status_code == 404


@pytest.mark.django_db
def test_connection_lifecycle(user, auth_client, run_events):
    other = UserFactory(username="sami")
    oc = client_for(other)
    with run_events():
        sent = auth_client.post("/api/connections/", {"username": "sami"})
    assert sent.status_code == 201 and sent.data["direction"] == "outgoing"
    assert Notification.objects.filter(recipient=other, kind="connection_request").exists()
    assert auth_client.post("/api/connections/", {"username": "sami"}).status_code == 400

    incoming = oc.get("/api/connections/?status=incoming").data["results"]
    assert [c["person"]["username"] for c in incoming] == [user.username]
    rel = auth_client.get("/api/network/sami/").data["connection"]
    assert rel == {"id": sent.data["id"], "status": "pending", "direction": "outgoing"}

    cid = sent.data["id"]
    assert auth_client.post(f"/api/connections/{cid}/accept/").status_code == 403, "only addressee"
    stranger = client_for(UserFactory())
    assert stranger.post(f"/api/connections/{cid}/accept/").status_code == 404
    with run_events():
        assert oc.post(f"/api/connections/{cid}/accept/").data["status"] == "accepted"
    assert Notification.objects.filter(recipient=user, kind="connection_accepted").exists()
    assert [
        c["person"]["username"] for c in auth_client.get("/api/connections/").data["results"]
    ] == ["sami"]
    assert auth_client.get("/api/network/sami/").data["connections"] == 1

    assert auth_client.delete(f"/api/connections/{cid}/").status_code == 204
    assert not Connection.objects.exists()


@pytest.mark.django_db
def test_asking_back_accepts_and_decline_frees_the_pair(user, auth_client):
    other = UserFactory(username="sami")
    oc = client_for(other)
    cid = oc.post("/api/connections/", {"username": user.username}).data["id"]
    assert auth_client.post("/api/connections/", {"username": "sami"}).data["status"] == "accepted"
    Connection.objects.all().delete()

    cid = oc.post("/api/connections/", {"username": user.username}).data["id"]
    assert oc.post(f"/api/connections/{cid}/decline/").status_code == 403
    assert auth_client.post(f"/api/connections/{cid}/decline/").status_code == 204
    assert oc.post("/api/connections/", {"username": user.username}).status_code == 201


@pytest.mark.django_db
def test_database_keeps_one_row_per_pair(user):
    other = UserFactory()
    Connection.objects.create(requester=user, addressee=other)
    with pytest.raises(IntegrityError):
        Connection.objects.create(requester=other, addressee=user)


@pytest.mark.django_db
def test_no_self_follow_in_the_database(user):
    with pytest.raises(IntegrityError):
        Follow.objects.create(follower=user, following=user)


@pytest.mark.django_db
def test_suggestions_rank_by_shared_skills(user, auth_client):
    django, sql, vue = (Skill.objects.create(name=n) for n in ("Django", "SQL", "Vue"))
    for s in (django, sql):
        ProfileSkill.objects.create(profile=user.profile, skill=s)
    two, one, none, linked = (UserFactory(username=n) for n in ("two", "one", "none", "linked"))
    for p, skills in ((two, (django, sql)), (one, (sql,)), (none, (vue,)), (linked, (django,))):
        for s in skills:
            ProfileSkill.objects.create(profile=p.profile, skill=s)
    Connection.objects.create(requester=user, addressee=linked)

    data = auth_client.get("/api/network/suggestions/").data
    assert [(d["username"], d["shared_skills"]) for d in data] == [("two", 2), ("one", 1)]
