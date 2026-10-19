from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.test import APIClient

from apps.community.models import Event, Group, Membership
from apps.network.models import Connection, Follow
from apps.notifications.models import Notification
from conftest import UserFactory


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture
def run_events(django_capture_on_commit_callbacks):
    return lambda: django_capture_on_commit_callbacks(execute=True)


@pytest.fixture
def owner(db):
    return UserFactory(first_name="Hala", last_name="Aziz")


def make_group(owner, privacy="public", name="Django Amman"):
    return client_for(owner).post("/api/groups/", {"name": name, "privacy": privacy}).data


@pytest.mark.django_db
def test_public_group_join_post_and_leave(owner, user, auth_client):
    g = make_group(owner)
    assert g["slug"] == "django-amman" and g["my_role"] == "owner" and g["member_count"] == 1
    assert make_group(owner)["slug"] == "django-amman-2", "slugs stay unique"

    assert (
        auth_client.post("/api/posts/", {"body": "hi", "group_slug": g["slug"]}).status_code == 403
    )
    assert auth_client.post(f"/api/groups/{g['slug']}/join/").data["my_status"] == "active"
    assert (
        auth_client.post("/api/posts/", {"body": "hi", "group_slug": g["slug"]}).status_code == 201
    )
    assert [
        p["body"] for p in auth_client.get(f"/api/groups/{g['slug']}/posts/").data["results"]
    ] == ["hi"]

    assert client_for(owner).post(f"/api/groups/{g['slug']}/leave/").status_code == 400
    assert auth_client.post(f"/api/groups/{g['slug']}/leave/").data["my_status"] is None
    mine = auth_client.get("/api/groups/?mine=true").data["results"]
    assert mine == []


@pytest.mark.django_db
def test_private_group_requests_need_approval(owner, user, auth_client, run_events):
    g = make_group(owner, "private", "Reading circle")
    slug = g["slug"]
    client_for(owner).post("/api/posts/", {"body": "members only", "group_slug": slug})

    assert auth_client.get(f"/api/groups/{slug}/").status_code == 200, "listed"
    assert auth_client.get(f"/api/groups/{slug}/posts/").status_code == 404, "content is private"
    assert auth_client.get(f"/api/groups/{slug}/members/").status_code == 404

    with run_events():
        assert auth_client.post(f"/api/groups/{slug}/join/").data["my_status"] == "pending"
    assert Notification.objects.filter(recipient=owner, kind="group_request").exists()
    assert auth_client.get(f"/api/groups/{slug}/posts/").status_code == 404

    assert auth_client.get(f"/api/groups/{slug}/members/?status=pending").status_code == 404
    pending = client_for(owner).get(f"/api/groups/{slug}/members/?status=pending").data["results"]
    assert [m["user_id"] for m in pending] == [user.id]
    stranger = client_for(UserFactory())
    assert stranger.post(f"/api/groups/{slug}/members/{user.id}/approve/").status_code == 403

    with run_events():
        assert (
            client_for(owner).post(f"/api/groups/{slug}/members/{user.id}/approve/").status_code
            == 200
        )
    assert Notification.objects.filter(recipient=user, kind="group_approved").exists()
    posts = auth_client.get(f"/api/groups/{slug}/posts/").data["results"]
    assert [p["body"] for p in posts] == ["members only"]

    post_id = posts[0]["id"]
    assert stranger.get(f"/api/posts/{post_id}/").status_code == 404
    assert stranger.get(f"/api/engagement/post/{post_id}/comments/").status_code == 404


@pytest.mark.django_db
def test_roles_and_removal(owner, user, auth_client):
    slug = make_group(owner)["slug"]
    auth_client.post(f"/api/groups/{slug}/join/")
    other = UserFactory()
    client_for(other).post(f"/api/groups/{slug}/join/")

    assert auth_client.delete(f"/api/groups/{slug}/members/{other.id}/").status_code == 403
    oc = client_for(owner)
    assert (
        oc.patch(f"/api/groups/{slug}/members/{user.id}/", {"role": "admin"}).data["role"]
        == "admin"
    )
    assert auth_client.delete(f"/api/groups/{slug}/members/{other.id}/").status_code == 204
    assert auth_client.delete(f"/api/groups/{slug}/members/{owner.id}/").status_code == 400
    assert (
        oc.patch(f"/api/groups/{slug}/members/{owner.id}/", {"role": "member"}).status_code == 400
    )
    assert auth_client.patch(f"/api/groups/{slug}/", {"description": "Meetups"}).status_code == 200
    assert auth_client.delete(f"/api/groups/{slug}/").status_code == 403
    assert oc.delete(f"/api/groups/{slug}/").status_code == 204
    with pytest.raises(IntegrityError):
        g = Group.objects.create(name="x", owner=owner)
        Membership.objects.create(group=g, user=owner)
        Membership.objects.create(group=g, user=owner)


@pytest.mark.django_db
def test_feed_and_profile_posts(owner, user, auth_client):
    followed, connected, stranger = UserFactory(), UserFactory(), UserFactory()
    Follow.objects.create(follower=user, following=followed)
    Connection.objects.create(requester=connected, addressee=user, status="accepted")
    slug = make_group(owner, "private", "Inner circle")["slug"]
    for author, body in ((followed, "followed"), (connected, "connected"), (stranger, "stranger")):
        client_for(author).post("/api/posts/", {"body": body})
    client_for(owner).post("/api/posts/", {"body": "secret", "group_slug": slug})
    auth_client.post("/api/posts/", {"body": "mine"})

    feed = [p["body"] for p in auth_client.get("/api/posts/").data["results"]]
    assert feed == ["mine", "connected", "followed"]
    by_owner = auth_client.get(f"/api/posts/?author={owner.username}").data["results"]
    assert by_owner == [], "group posts you cannot read stay out of a profile"


@pytest.mark.django_db
def test_post_edit_delete_comments_and_reactions(owner, user, auth_client, run_events):
    pid = auth_client.post(
        "/api/posts/", {"body": "Our study group meets on Thursdays at six"}
    ).data["id"]
    other = client_for(owner)
    assert other.patch(f"/api/posts/{pid}/", {"body": "x"}).status_code == 403
    assert other.delete(f"/api/posts/{pid}/").status_code == 403
    with run_events():
        other.post(f"/api/engagement/post/{pid}/comments/", {"body": "I will come"})
    other.put(f"/api/engagement/post/{pid}/reactions/", {"kind": "celebrate"})
    n = Notification.objects.get(recipient=user, kind="comment")
    assert n.title == "Hala Aziz commented on “Our study group meets on Thursdays at si…”"

    post = auth_client.get(f"/api/posts/{pid}/").data
    assert post["comment_count"] == 1 and post["reactions"]["counts"] == {"celebrate": 1}
    edited = auth_client.patch(f"/api/posts/{pid}/", {"body": "Thursdays at seven"}).data
    assert edited["edited"] and edited["body"] == "Thursdays at seven"
    assert auth_client.delete(f"/api/posts/{pid}/").status_code == 204


@pytest.mark.django_db
def test_group_managers_moderate_posts(owner, user, auth_client):
    slug = make_group(owner)["slug"]
    auth_client.post(f"/api/groups/{slug}/join/")
    pid = auth_client.post("/api/posts/", {"body": "spam", "group_slug": slug}).data["id"]
    assert client_for(owner).delete(f"/api/posts/{pid}/").status_code == 204


@pytest.mark.django_db
def test_events_rsvp_and_capacity(owner, user, auth_client, run_events):
    soon = timezone.now() + timedelta(days=2)
    oc = client_for(owner)
    bad = oc.post(
        "/api/events/",
        {"title": "x", "starts_at": soon, "ends_at": soon - timedelta(hours=1), "location": "Hall"},
    )
    assert bad.status_code == 400
    assert (
        oc.post(
            "/api/events/", {"title": "x", "starts_at": soon, "ends_at": soon + timedelta(hours=1)}
        ).status_code
        == 400
    )

    eid = oc.post(
        "/api/events/",
        {
            "title": "Django meetup",
            "starts_at": soon,
            "ends_at": soon + timedelta(hours=2),
            "location": "Amman",
            "capacity": 1,
        },
    ).data["id"]
    with run_events():
        e = auth_client.put(f"/api/events/{eid}/rsvp/", {"status": "going"}).data
        auth_client.put(f"/api/events/{eid}/rsvp/", {"status": "going"})
    assert e["going_count"] == 1 and e["my_status"] == "going"
    assert Notification.objects.filter(recipient=owner, kind="event_rsvp").count() == 1

    late = client_for(UserFactory())
    assert late.put(f"/api/events/{eid}/rsvp/", {"status": "going"}).status_code == 400, "full"
    assert late.put(f"/api/events/{eid}/rsvp/", {"status": "interested"}).status_code == 200
    assert auth_client.delete(f"/api/events/{eid}/rsvp/").data["my_status"] is None
    assert late.put(f"/api/events/{eid}/rsvp/", {"status": "going"}).status_code == 200

    assert [x["title"] for x in auth_client.get("/api/events/").data["results"]] == [
        "Django meetup"
    ]
    assert auth_client.get("/api/events/?when=past").data["results"] == []
    assert auth_client.patch(f"/api/events/{eid}/", {"title": "y"}).status_code == 403


@pytest.mark.django_db
def test_group_events_follow_group_privacy(owner, user, auth_client):
    slug = make_group(owner, "private", "Inner circle")["slug"]
    soon = timezone.now() + timedelta(days=1)
    oc = client_for(owner)
    created = oc.post(
        "/api/events/",
        {
            "title": "Members night",
            "starts_at": soon,
            "ends_at": soon + timedelta(hours=1),
            "online_url": "https://meet.example.com/x",
            "group_slug": slug,
        },
    )
    assert created.status_code == 201
    assert auth_client.get("/api/events/").data["results"] == []
    assert auth_client.get(f"/api/events/{created.data['id']}/").status_code == 404
    assert (
        auth_client.post(
            "/api/events/",
            {
                "title": "x",
                "starts_at": soon,
                "ends_at": soon + timedelta(hours=1),
                "location": "y",
                "group_slug": slug,
            },
        ).status_code
        == 403
    )
    assert Event.objects.count() == 1


@pytest.mark.django_db
def test_group_members_come_in_pages(user, auth_client):
    from apps.community.models import Group, Membership

    group = Group.objects.create(owner=user, name="Big", slug="big")
    Membership.objects.create(group=group, user=user, status="active", role="owner")
    for _ in range(25):
        Membership.objects.create(group=group, user=UserFactory(), status="active")
    first = auth_client.get("/api/groups/big/members/").json()
    assert len(first["results"]) == 20 and first["next"]
    assert first["results"][0]["role"] == "owner", "who joined first leads"
    assert len(auth_client.get(first["next"]).json()["results"]) == 6
