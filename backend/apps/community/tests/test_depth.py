import io
from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.community.models import Attendance, Event, Group, Membership, Post, PostImage
from apps.notifications.models import Notification
from conftest import UserFactory


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture
def run_events(django_capture_on_commit_callbacks):
    return lambda: django_capture_on_commit_callbacks(execute=True)


@pytest.fixture(autouse=True)
def media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path


def photo(name="p.jpg", size=(3000, 1500)):
    exif = Image.Exif()
    exif[0x8825] = {2: (31, 57, 0)}  # a GPS block, as phone photos carry
    buf = io.BytesIO()
    Image.new("RGB", size, "teal").save(buf, "JPEG", exif=exif)
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


@pytest.mark.django_db
def test_post_with_images_is_cleaned(auth_client):
    r = auth_client.post(
        "/api/posts/", {"body": "", "images": [photo(), photo()]}, format="multipart"
    )
    assert r.status_code == 201, r.data
    assert [(i["width"], i["height"]) for i in r.data["images"]] == [(2000, 1000)] * 2
    stored = PostImage.objects.first().image
    with Image.open(stored) as img:
        assert img.format == "JPEG" and not img.getexif().get(0x8825), "location data is gone"

    assert auth_client.post("/api/posts/", {"body": ""}).status_code == 400
    five = {"body": "x", "images": [photo() for _ in range(5)]}
    assert auth_client.post("/api/posts/", five, format="multipart").status_code == 400
    fake = SimpleUploadedFile("x.jpg", b"not an image", content_type="image/jpeg")
    bad = auth_client.post("/api/posts/", {"body": "x", "images": [fake]}, format="multipart")
    assert bad.status_code == 400 and Post.objects.count() == 1, "nothing saved on a bad image"


@pytest.mark.django_db
def test_share_points_at_the_original_and_notifies(user, auth_client, run_events):
    author = UserFactory()
    original = Post.objects.create(author=author, body="Read this")
    with run_events():
        r = auth_client.post(f"/api/posts/{original.id}/share/", {"body": "Worth it"})
    assert r.status_code == 201, r.data
    assert r.data["shared_from"]["id"] == original.id and r.data["body"] == "Worth it"
    assert Notification.objects.filter(recipient=author, kind="post_shared").exists()

    again = client_for(UserFactory()).post(f"/api/posts/{r.data['id']}/share/")
    assert again.data["shared_from"]["id"] == original.id, "a share of a share is the original"
    assert auth_client.get(f"/api/posts/{original.id}/").data["share_count"] == 2

    original.delete()
    assert not Post.objects.filter(shared_from__isnull=False).exists()


@pytest.mark.django_db
def test_private_group_posts_cannot_be_shared(user, auth_client):
    owner = UserFactory()
    group = Group.objects.create(owner=owner, name="Core", slug="core", privacy="private")
    for member in (owner, user):
        Membership.objects.create(group=group, user=member, status="active")
    post = Post.objects.create(author=owner, group=group, body="Internal")
    assert auth_client.post(f"/api/posts/{post.id}/share/").status_code == 403


@pytest.mark.django_db
def test_event_feedback_after_the_event(user, auth_client):
    host = UserFactory()
    start = timezone.now() - timedelta(days=1)
    event = Event.objects.create(
        host=host,
        title="Meetup",
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        location="Amman",
    )
    url = f"/api/events/{event.id}/feedback/"
    assert auth_client.put(url, {"rating": 5}).status_code == 403, "only people who went"
    Attendance.objects.create(event=event, user=user, status="going")
    assert auth_client.put(url, {"rating": 9}).status_code == 400
    assert auth_client.put(url, {"rating": 4, "comment": "Great talks"}).status_code == 200
    assert auth_client.put(url, {"rating": 5}).data["rating"] == 5, "a second answer replaces"

    other = UserFactory()
    Attendance.objects.create(event=event, user=other, status="going")
    client_for(other).put(url, {"rating": 3})
    shown = auth_client.get(f"/api/events/{event.id}/").data
    assert (shown["rating"], shown["rating_count"], shown["my_rating"]) == (4.0, 2, 5)
    assert auth_client.get(url).status_code == 403
    assert [f["rating"] for f in client_for(host).get(url).data] == [3, 5]

    future = Event.objects.create(
        host=host,
        title="Later",
        starts_at=timezone.now() + timedelta(days=1),
        ends_at=timezone.now() + timedelta(days=1, hours=1),
        location="Amman",
    )
    Attendance.objects.create(event=future, user=user, status="going")
    assert auth_client.put(f"/api/events/{future.id}/feedback/", {"rating": 5}).status_code == 400


@pytest.mark.django_db
def test_events_list_counts_stay_right_with_feedback(user, auth_client):
    start = timezone.now() - timedelta(days=1)
    event = Event.objects.create(
        host=user, title="Past", starts_at=start, ends_at=start + timedelta(hours=1), location="x"
    )
    for _ in range(3):
        u = UserFactory()
        Attendance.objects.create(event=event, user=u, status="going")
        client_for(u).put(f"/api/events/{event.id}/feedback/", {"rating": 4})
    row = auth_client.get("/api/events/?when=past").data["results"][0]
    assert (row["going_count"], row["rating_count"], row["rating"]) == (3, 3, 4.0)
