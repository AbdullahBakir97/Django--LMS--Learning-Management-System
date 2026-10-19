import pytest
from rest_framework.test import APIClient

from apps.community.models import Group, Post
from apps.engagement.models import Comment
from apps.moderation.models import Report
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
def moderator(db):
    return UserFactory(role="admin")


@pytest.fixture
def post(db):
    return Post.objects.create(author=UserFactory(username="spammer"), body="Buy followers now")


def report(client, kind, pk, reason="spam", **extra):
    return client.post("/api/reports/", {"kind": kind, "object_id": pk, "reason": reason, **extra})


@pytest.mark.django_db
def test_report_rules(user, auth_client, post):
    assert report(auth_client, "post", post.id).status_code == 201
    assert report(auth_client, "post", post.id).status_code == 200, "once per person"
    assert Report.objects.count() == 1
    assert report(auth_client, "user", user.id).status_code == 400, "not yourself"
    own = Post.objects.create(author=user, body="mine")
    assert report(auth_client, "post", own.id).status_code == 400
    assert report(auth_client, "post", 99999).status_code == 404
    assert report(auth_client, "nope", post.id).status_code == 400
    assert report(auth_client, "post", post.id, reason="bored").status_code == 400

    owner = UserFactory()
    hidden = Group.objects.create(owner=owner, name="Core", slug="core", privacy="private")
    secret = Post.objects.create(author=owner, group=hidden, body="internal")
    assert report(auth_client, "post", secret.id).status_code == 404, "what you cannot see"


@pytest.mark.django_db
def test_queue_is_staff_only_and_grouped(post, auth_client, moderator):
    report(auth_client, "post", post.id)
    report(client_for(UserFactory()), "post", post.id, reason="harassment", details="Again")
    assert auth_client.get("/api/moderation/queue/").status_code == 403
    (item,) = client_for(moderator).get("/api/moderation/queue/").data
    assert item["kind"] == "post" and item["report_count"] == 2
    assert item["reasons"] == {"spam": 1, "harassment": 1}
    assert item["preview"]["author"] == "spammer" and item["preview"]["url"] == f"/posts/{post.id}"


@pytest.mark.django_db
def test_removing_resolves_every_report_and_tells_reporters(
    post, user, auth_client, moderator, run_events
):
    other = UserFactory()
    report(auth_client, "post", post.id)
    report(client_for(other), "post", post.id)
    url = f"/api/moderation/post/{post.id}/resolve/"
    assert auth_client.post(url, {"action": "remove"}).status_code == 403
    with run_events():
        r = client_for(moderator).post(url, {"action": "remove", "note": "Spam"})
    assert r.data == {"resolved": 2}
    assert not Post.objects.filter(pk=post.id).exists()
    assert set(Report.objects.values_list("status", flat=True)) == {"removed"}
    reviewed = Notification.objects.filter(kind="report_reviewed")
    assert set(reviewed.values_list("recipient_id", flat=True)) == {user.id, other.id}
    assert client_for(moderator).get("/api/moderation/queue/").data == []
    assert client_for(moderator).post(url, {"action": "remove"}).status_code == 400


@pytest.mark.django_db
def test_dismiss_keeps_content_and_removing_a_person_deactivates(post, auth_client, moderator):
    report(auth_client, "post", post.id)
    client_for(moderator).post(f"/api/moderation/post/{post.id}/resolve/", {"action": "dismiss"})
    assert Post.objects.filter(pk=post.id).exists()
    assert Report.objects.get().status == "dismissed"

    report(auth_client, "user", post.author_id, reason="harassment")
    client_for(moderator).post(
        f"/api/moderation/user/{post.author_id}/resolve/", {"action": "remove"}
    )
    post.author.refresh_from_db()
    assert post.author.is_active is False


@pytest.mark.django_db
def test_comments_are_soft_deleted(post, user, auth_client, moderator):
    comment = Comment.objects.create(
        author=post.author, target_type="post", target_id=post.id, body="rude words"
    )
    assert report(auth_client, "comment", comment.id, reason="harassment").status_code == 201
    (item,) = client_for(moderator).get("/api/moderation/queue/").data
    assert item["preview"]["excerpt"] == "rude words"
    client_for(moderator).post(
        f"/api/moderation/comment/{comment.id}/resolve/", {"action": "remove"}
    )
    comment.refresh_from_db()
    assert comment.deleted_at is not None and comment.body == ""
    assert report(client_for(UserFactory()), "comment", comment.id).status_code == 404


@pytest.mark.django_db
def test_a_deactivated_account_loses_access_at_once(moderator, auth_client):
    from allauth.account.models import EmailAddress

    person = UserFactory(username="troll")
    EmailAddress.objects.create(user=person, email=person.email, verified=True, primary=True)
    browser = APIClient()
    signed_in = browser.post(
        "/api/auth/login/", {"email": person.email, "password": "pass-word-123"}
    )
    assert signed_in.status_code == 200, signed_in.data
    access = signed_in.data["access"]

    report(auth_client, "user", person.id, reason="harassment")
    client_for(moderator).post(f"/api/moderation/user/{person.id}/resolve/", {"action": "remove"})

    browser.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert browser.get("/api/auth/user/").status_code == 401, "the access token stops working"
    browser.credentials()
    assert browser.post("/api/auth/token/refresh/").status_code == 401, "and cannot be renewed"


@pytest.mark.django_db
def test_admins_cannot_be_deactivated_from_reports(moderator, auth_client):
    other_admin = UserFactory(role="admin")
    report(auth_client, "user", other_admin.id, reason="other")
    r = client_for(moderator).post(
        f"/api/moderation/user/{other_admin.id}/resolve/", {"action": "remove"}
    )
    assert r.status_code == 400
    other_admin.refresh_from_db()
    assert other_admin.is_active
