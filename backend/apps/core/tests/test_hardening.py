"""Release guards: rate limits on auth, and list endpoints whose query count does not grow."""

from datetime import timedelta

import pytest
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.careers.models import Company, Job
from apps.community.models import Event, Post
from apps.core.throttling import AuthRateThrottle
from apps.learning.models import Course, Lesson
from apps.messaging.models import Conversation, Message, Participant
from apps.network.models import Connection, Follow
from apps.notifications.models import Notification
from conftest import UserFactory


@pytest.mark.django_db
def test_sign_in_is_rate_limited_per_client(monkeypatch):
    cache.clear()
    monkeypatch.setattr(AuthRateThrottle, "THROTTLE_RATES", {"auth": "3/min"})
    client = APIClient()
    codes = [
        client.post("/api/auth/login/", {"email": "x@example.com", "password": "nope"}).status_code
        for _ in range(4)
    ]
    assert codes == [400, 400, 400, 429]
    limited = client.post("/api/auth/login/", {"email": "x@example.com", "password": "nope"})
    assert limited["Content-Type"].startswith("application/problem+json")
    assert "Retry-After" in limited
    cache.clear()


def _queries(client, url) -> int:
    with CaptureQueriesContext(connection) as ctx:
        assert client.get(url).status_code == 200
    return len(ctx.captured_queries)


def _grow(make, client, url):
    """Queries for a list must not depend on how many rows it shows."""
    make(3)
    small = _queries(client, url)
    make(9)
    large = _queries(client, url)
    assert large == small, f"{url}: {small} queries for 3 rows, {large} for 12"


@pytest.fixture
def me(db):
    return UserFactory()


@pytest.fixture
def client(me):
    c = APIClient()
    c.force_authenticate(me)
    return c


@pytest.mark.django_db
def test_feed_queries_are_flat(me, client):
    def make(n):
        for _ in range(n):
            author = UserFactory()
            Follow.objects.create(follower=me, following=author)
            Post.objects.create(author=author, body="hello")

    _grow(make, client, "/api/posts/")


@pytest.mark.django_db
def test_jobs_queries_are_flat(me, client):
    company = Company.objects.create(name="Acme")

    def make(n):
        for i in range(n):
            Job.objects.create(company=company, title=f"Job {i}", description="d", status="open")

    _grow(make, client, "/api/jobs/")


@pytest.mark.django_db
def test_courses_queries_are_flat(me, client):
    teacher = UserFactory(role="instructor")

    def make(n):
        for _ in range(n):
            c = Course.objects.create(instructor=teacher, title="Course", status="published")
            Lesson.objects.create(course=c, title="L", order=1)

    _grow(make, client, "/api/courses/")


@pytest.mark.django_db
def test_conversations_queries_are_flat(me, client):
    def make(n):
        for _ in range(n):
            other = UserFactory()
            Connection.objects.create(requester=me, addressee=other, status="accepted")
            c = Conversation.objects.create(direct_key=Conversation.key_for(me.id, other.id))
            Participant.objects.bulk_create(
                [Participant(conversation=c, user=u) for u in (me, other)]
            )
            Message.objects.create(conversation=c, sender=other, body="hi")

    _grow(make, client, "/api/conversations/")


@pytest.mark.django_db
def test_notifications_and_events_queries_are_flat(me, client):
    host = UserFactory()
    soon = timezone.now() + timedelta(days=1)

    def make(n):
        for _ in range(n):
            Notification.objects.create(recipient=me, actor=host, kind="follow", title="t")
            Event.objects.create(
                host=host,
                title="E",
                starts_at=soon,
                ends_at=soon + timedelta(hours=1),
                location="x",
            )

    _grow(make, client, "/api/notifications/")
    _grow(lambda n: None, client, "/api/events/")
