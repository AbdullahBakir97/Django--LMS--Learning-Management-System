import factory
import pytest
from rest_framework.test import APIClient

from apps.learning.models import Certificate, Course, Enrollment, Lesson
from conftest import UserFactory


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Course

    instructor = factory.SubFactory(UserFactory, role="instructor")
    title = factory.Sequence(lambda n: f"Course {n}")
    status = Course.Status.PUBLISHED


class LessonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Lesson

    course = factory.SubFactory(CourseFactory)
    title = factory.Sequence(lambda n: f"Lesson {n}")
    order = factory.Sequence(lambda n: n + 1)
    content = "Read this."


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture
def instructor(db):
    return UserFactory(role="instructor")


@pytest.fixture
def course(instructor):
    c = CourseFactory(instructor=instructor)
    LessonFactory(course=c, order=1, is_free_preview=True)
    LessonFactory(course=c, order=2)
    return c


QUIZ = {
    "title": "Check",
    "pass_score": 50,
    "questions": [
        {
            "text": "2+2?",
            "order": 1,
            "choices": [{"text": "4", "is_correct": True}, {"text": "5", "is_correct": False}],
        },
        {
            "text": "3+3?",
            "order": 2,
            "choices": [{"text": "6", "is_correct": True}, {"text": "7", "is_correct": False}],
        },
    ],
}


@pytest.mark.django_db
def test_learners_cannot_author_courses(auth_client):
    assert auth_client.post("/api/courses/", {"title": "Nope"}).status_code == 403


@pytest.mark.django_db
def test_instructor_creates_and_publishes(instructor):
    c = client_for(instructor)
    response = c.post("/api/courses/", {"title": "Django from scratch", "summary": "APIs"})
    assert response.status_code == 201, response.data
    slug = response.data["slug"]
    assert slug == "django-from-scratch"
    assert response.data["status"] == "draft"

    assert c.post(f"/api/courses/{slug}/publish/").status_code == 400, "needs a lesson"
    assert (
        c.post(f"/api/courses/{slug}/lessons/", {"title": "Intro", "order": 1}).status_code == 201
    )
    assert c.post(f"/api/courses/{slug}/lessons/", {"title": "Dup", "order": 1}).status_code == 400
    response = c.post(f"/api/courses/{slug}/publish/")
    assert response.status_code == 200
    assert response.data["status"] == "published"


@pytest.mark.django_db
def test_drafts_are_private_to_their_instructor(instructor, auth_client):
    draft = CourseFactory(instructor=instructor, status=Course.Status.DRAFT)
    assert auth_client.get(f"/api/courses/{draft.slug}/").status_code == 404
    assert client_for(instructor).get(f"/api/courses/{draft.slug}/").status_code == 200
    other = client_for(UserFactory(role="instructor"))
    assert other.patch(f"/api/courses/{draft.slug}/", {"title": "Hijack"}).status_code == 404
    preview = LessonFactory(course=draft, is_free_preview=True)
    assert auth_client.get(f"/api/courses/{draft.slug}/lessons/{preview.id}/").status_code == 404


@pytest.mark.django_db
def test_enrollment_rules(course, auth_client, instructor):
    assert client_for(instructor).post(f"/api/courses/{course.slug}/enroll/").status_code == 400
    assert auth_client.post(f"/api/courses/{course.slug}/enroll/").status_code == 201
    assert auth_client.post(f"/api/courses/{course.slug}/enroll/").status_code == 400
    assert Enrollment.objects.filter(course=course).count() == 1

    advanced = CourseFactory(instructor=instructor)
    advanced.prerequisites.add(course)
    response = auth_client.post(f"/api/courses/{advanced.slug}/enroll/")
    assert response.status_code == 400
    assert "prerequisites" in response.data["errors"]


@pytest.mark.django_db
def test_lesson_content_is_gated(course, auth_client):
    preview, locked = course.lessons.order_by("order")
    assert auth_client.get(f"/api/courses/{course.slug}/").status_code == 200
    assert auth_client.patch(f"/api/courses/{course.slug}/", {"title": "x"}).status_code == 403
    assert auth_client.get(f"/api/courses/{course.slug}/lessons/{preview.id}/").status_code == 200
    assert auth_client.get(f"/api/courses/{course.slug}/lessons/{locked.id}/").status_code == 403
    assert (
        auth_client.post(f"/api/courses/{course.slug}/lessons/{locked.id}/complete/").status_code
        == 403
    )
    auth_client.post(f"/api/courses/{course.slug}/enroll/")
    assert auth_client.get(f"/api/courses/{course.slug}/lessons/{locked.id}/").status_code == 200


@pytest.mark.django_db
def test_completion_issues_certificate_and_verifies_publicly(
    course, auth_client, instructor, user, django_capture_on_commit_callbacks
):
    first, second = course.lessons.order_by("order")
    ic = client_for(instructor)
    assert ic.put(f"/api/lessons/{second.id}/quiz/", QUIZ, format="json").status_code == 201
    auth_client.post(f"/api/courses/{course.slug}/enroll/")

    quiz = auth_client.get(f"/api/lessons/{second.id}/quiz/").data
    assert "is_correct" not in quiz["questions"][0]["choices"][0], "answers must stay hidden"

    auth_client.post(f"/api/courses/{course.slug}/lessons/{first.id}/complete/")
    progress = auth_client.get(f"/api/courses/{course.slug}/progress/").data
    assert progress["status"] == "active" and progress["completed_lessons"] == [first.id]

    wrong = {q["id"]: q["choices"][1]["id"] for q in quiz["questions"]}
    response = auth_client.post(
        f"/api/lessons/{second.id}/quiz/submit/", {"answers": wrong}, format="json"
    )
    assert response.status_code == 201 and response.data == {
        **response.data,
        "score": 0,
        "passed": False,
    }

    right = {q["id"]: q["choices"][0]["id"] for q in quiz["questions"]}
    with django_capture_on_commit_callbacks(execute=True):
        response = auth_client.post(
            f"/api/lessons/{second.id}/quiz/submit/", {"answers": right}, format="json"
        )
    assert response.data["score"] == 100 and response.data["passed"]

    progress = auth_client.get(f"/api/courses/{course.slug}/progress/").data
    assert progress["status"] == "completed"
    code = progress["certificate_code"]
    certificate = Certificate.objects.get(code=code)
    assert certificate.pdf.name.endswith(".pdf"), "the eager Celery task rendered the PDF"

    response = APIClient().get(f"/api/certificates/{code}/")
    assert response.status_code == 200
    assert response.data["course"] == course.title
    assert response.data["student"] == user.get_full_name()


@pytest.mark.django_db
def test_my_enrollments(course, auth_client):
    auth_client.post(f"/api/courses/{course.slug}/enroll/")
    response = auth_client.get("/api/me/enrollments/")
    assert [e["course"]["slug"] for e in response.data["results"]] == [course.slug]
