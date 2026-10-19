import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.learning.models import Enrollment, Quiz
from apps.learning.tests.test_learning import CourseFactory, LessonFactory, client_for
from apps.payments.models import Order
from conftest import UserFactory


@pytest.fixture
def paid(db):
    course = CourseFactory(price_cents=2900)
    LessonFactory(course=course, order=1, is_free_preview=True, video_url="https://v/1")
    LessonFactory(course=course, order=2, content="SECRET", video_url="https://v/2")
    return course


@pytest.mark.django_db
def test_locked_lessons_stay_locked_in_lists(paid):
    stranger = client_for(UserFactory())
    lessons = stranger.get(f"/api/courses/{paid.slug}/lessons/").json()
    assert [lesson["order"] for lesson in lessons] == [1], "only the free preview"
    outline = stranger.get(f"/api/courses/{paid.slug}/").json()["lessons"]
    assert [(lesson["video_url"], lesson["has_quiz"]) for lesson in outline] == [
        ("https://v/1", False),
        ("", False),
    ]
    learner = UserFactory()
    Enrollment.objects.create(course=paid, student=learner)
    assert len(client_for(learner).get(f"/api/courses/{paid.slug}/lessons/").json()) == 2
    owner_view = client_for(paid.instructor).get(f"/api/courses/{paid.slug}/").json()
    assert owner_view["lessons"][1]["video_url"] == "https://v/2"


@pytest.mark.django_db
def test_quizzes_of_draft_courses_are_hidden(db):
    draft = CourseFactory(status="draft")
    lesson = LessonFactory(course=draft, is_free_preview=True)
    Quiz.objects.create(lesson=lesson, title="Q")
    assert client_for(UserFactory()).get(f"/api/lessons/{lesson.id}/quiz/").status_code == 404
    assert client_for(draft.instructor).get(f"/api/lessons/{lesson.id}/quiz/").status_code == 200


@pytest.mark.django_db
def test_a_course_with_learners_or_orders_cannot_be_deleted(paid):
    owner = client_for(paid.instructor)
    Order.objects.create(buyer=UserFactory(), course=paid, amount_cents=2900, currency="usd")
    assert owner.delete(f"/api/courses/{paid.slug}/").status_code == 400
    empty = CourseFactory(instructor=paid.instructor)
    assert owner.delete(f"/api/courses/{empty.slug}/").status_code == 204


@pytest.mark.django_db
def test_attachments_refuse_pages_and_scripts(paid):
    owner = client_for(paid.instructor)
    lesson = paid.lessons.get(order=2)
    url = f"/api/courses/{paid.slug}/lessons/{lesson.id}/attachments/"
    page = SimpleUploadedFile("x.html", b"<script>alert(1)</script>", content_type="text/html")
    assert owner.post(url, {"title": "x", "file": page}, format="multipart").status_code == 400
    pdf = SimpleUploadedFile("notes.pdf", b"%PDF-1.4", content_type="application/pdf")
    assert owner.post(url, {"title": "Notes", "file": pdf}, format="multipart").status_code == 201


@pytest.mark.django_db
def test_attachments_download_only_for_readers_of_the_lesson(paid):
    lesson = paid.lessons.get(order=2)
    pdf = SimpleUploadedFile("notes.pdf", b"%PDF-1.4 notes", content_type="application/pdf")
    owner = client_for(paid.instructor)
    url = f"/api/courses/{paid.slug}/lessons/{lesson.id}/attachments/"
    created = owner.post(url, {"title": "Notes", "file": pdf}, format="multipart").json()
    assert "file" not in created and created["url"] == f"/api/attachments/{created['id']}/file/"
    assert client_for(UserFactory()).get(created["url"]).status_code == 403
    learner = UserFactory()
    Enrollment.objects.create(course=paid, student=learner)
    r = client_for(learner).get(created["url"])
    assert r.status_code == 200 and b"".join(r.streaming_content) == b"%PDF-1.4 notes"
    assert r["Content-Disposition"].startswith("attachment")
