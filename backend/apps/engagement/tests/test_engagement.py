import pytest
from rest_framework.test import APIClient

from apps.engagement.models import Comment
from apps.learning.models import Course, Lesson
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
def instructor(db):
    return UserFactory(role="instructor")


@pytest.fixture
def lessons(instructor):
    course = Course.objects.create(instructor=instructor, title="SQL", status="published")
    preview = Lesson.objects.create(course=course, title="Intro", order=1, is_free_preview=True)
    locked = Lesson.objects.create(course=course, title="Joins", order=2)
    return preview, locked


def url(lesson, what="comments"):
    return f"/api/engagement/lesson/{lesson.id}/{what}/"


@pytest.mark.django_db
def test_thread_with_replies_and_notifications(lessons, instructor, user, auth_client, run_events):
    preview, _ = lessons
    other = UserFactory(first_name="Omar", last_name="Saleh")
    with run_events():
        top = auth_client.post(url(preview), {"body": "Why use a CTE here?"}).data
        reply = client_for(other).post(url(preview), {"body": "Readability.", "parent": top["id"]})
    assert reply.status_code == 201

    kinds = set(Notification.objects.values_list("recipient_id", "kind"))
    assert (instructor.id, "comment") in kinds, "the instructor hears about new comments"
    assert (user.id, "reply") in kinds, "the parent author hears about replies"
    n = Notification.objects.get(recipient=user, kind="reply")
    assert n.title == "Omar Saleh replied to your comment on Intro"
    assert (
        n.url == f"/courses/{preview.course.slug}/lessons/{preview.id}#comment-{reply.data['id']}"
    )

    thread = auth_client.get(url(preview)).data["results"]
    assert [c["body"] for c in thread] == ["Why use a CTE here?"]
    assert [r["body"] for r in thread[0]["replies"]] == ["Readability."]
    assert thread[0]["can_edit"] and not thread[0]["replies"][0]["can_edit"]

    nested = auth_client.post(url(preview), {"body": "x", "parent": reply.data["id"]})
    assert nested.status_code == 400, "replies are one level deep"


@pytest.mark.django_db
def test_gated_lessons_hide_their_discussion(lessons, auth_client, instructor):
    _, locked = lessons
    assert auth_client.get(url(locked)).status_code == 404
    assert auth_client.post(url(locked), {"body": "hi"}).status_code == 404
    assert auth_client.get("/api/engagement/nothing/1/comments/").status_code == 404
    assert client_for(instructor).post(url(locked), {"body": "Notes"}).status_code == 201


@pytest.mark.django_db
def test_edit_and_delete_rules(lessons, instructor, user, auth_client):
    preview, _ = lessons
    cid = auth_client.post(url(preview), {"body": "first"}).data["id"]
    other = client_for(UserFactory())
    assert other.patch(f"/api/comments/{cid}/", {"body": "hijack"}).status_code == 403
    assert other.delete(f"/api/comments/{cid}/").status_code == 403

    edited = auth_client.patch(f"/api/comments/{cid}/", {"body": "first, fixed"}).data
    assert edited["edited"] and edited["body"] == "first, fixed"

    assert client_for(instructor).delete(f"/api/comments/{cid}/").status_code == 204, "moderation"
    assert Comment.objects.get(pk=cid).body == ""
    assert auth_client.get(url(preview)).data["results"] == [], "removed without replies: gone"
    assert auth_client.patch(f"/api/comments/{cid}/", {"body": "back"}).status_code == 404


@pytest.mark.django_db
def test_removed_comment_with_replies_stays_as_placeholder(lessons, auth_client):
    preview, _ = lessons
    top = auth_client.post(url(preview), {"body": "question"}).data["id"]
    client_for(UserFactory()).post(url(preview), {"body": "answer", "parent": top})
    auth_client.delete(f"/api/comments/{top}/")
    [placeholder] = auth_client.get(url(preview)).data["results"]
    assert placeholder["deleted"] and placeholder["body"] == ""
    assert [r["body"] for r in placeholder["replies"]] == ["answer"]


@pytest.mark.django_db
def test_reactions_on_lessons_and_comments(lessons, user, auth_client):
    preview, locked = lessons
    r = auth_client.put(url(preview, "reactions"), {"kind": "insightful"}).data
    assert r == {"counts": {"insightful": 1}, "mine": "insightful"}
    r = auth_client.put(url(preview, "reactions"), {"kind": "like"}).data
    assert r == {"counts": {"like": 1}, "mine": "like"}, "one reaction per person, changeable"
    client_for(UserFactory()).put(url(preview, "reactions"), {"kind": "like"})
    assert auth_client.get(url(preview, "reactions")).data["counts"] == {"like": 2}
    assert auth_client.delete(url(preview, "reactions")).data == {
        "counts": {"like": 1},
        "mine": None,
    }
    assert auth_client.put(url(preview, "reactions"), {"kind": "angry"}).status_code == 400
    assert auth_client.put(url(locked, "reactions"), {"kind": "like"}).status_code == 404

    cid = auth_client.post(url(preview), {"body": "nice"}).data["id"]
    client_for(UserFactory()).put(
        f"/api/engagement/comment/{cid}/reactions/", {"kind": "celebrate"}
    )
    [c] = auth_client.get(url(preview)).data["results"]
    assert c["reactions"] == {"counts": {"celebrate": 1}, "mine": None}
    assert (
        auth_client.post(f"/api/engagement/comment/{cid}/comments/", {"body": "x"}).status_code
        == 400
    )
