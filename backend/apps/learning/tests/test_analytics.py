from datetime import timedelta

import pytest
from django.utils import timezone

from apps.learning.models import Enrollment, LessonProgress, Quiz, QuizAttempt
from apps.learning.tests.test_learning import CourseFactory, LessonFactory, client_for
from conftest import UserFactory


@pytest.fixture
def setup(db):
    teacher = UserFactory(role="instructor")
    course = CourseFactory(instructor=teacher)
    lessons = [LessonFactory(course=course, order=i) for i in (1, 2, 3)]
    quiz = Quiz.objects.create(lesson=lessons[1], title="Check", pass_score=50)
    now = timezone.now()

    def enrol(days_ago, done, attempts=(), completed=False, last_days_ago=None):
        e = Enrollment.objects.create(course=course, student=UserFactory())
        when = now - timedelta(days=days_ago)
        Enrollment.objects.filter(pk=e.pk).update(
            created_at=when,
            status="completed" if completed else "active",
            completed_at=when + timedelta(days=4) if completed else None,
        )
        for lesson in lessons[:done]:
            p = LessonProgress.objects.create(enrollment=e, lesson=lesson)
            at = now - timedelta(days=last_days_ago if last_days_ago is not None else days_ago)
            LessonProgress.objects.filter(pk=p.pk).update(created_at=at)
        for score in attempts:
            QuizAttempt.objects.create(enrollment=e, quiz=quiz, score=score, passed=score >= 50)
        return e

    enrol(2, 3, attempts=(40, 80), completed=True)
    enrol(3, 2, attempts=(90,), last_days_ago=1)
    enrol(30, 1, last_days_ago=20)  # stalled: nothing for 20 days
    enrol(40, 0)  # stalled since enrolling
    return teacher, course


@pytest.mark.django_db
def test_course_analytics(setup):
    teacher, course = setup
    r = client_for(teacher).get(f"/api/courses/{course.slug}/analytics/")
    assert r.status_code == 200, r.data
    d = r.data
    assert (d["enrolled"], d["completed"], d["active"], d["completion_rate"]) == (4, 1, 3, 25)
    assert d["average_days_to_complete"] == 4.0
    assert [lesson["completed"] for lesson in d["lessons"]] == [3, 2, 1], "drop-off by lesson"
    (quiz,) = d["quizzes"]
    assert (quiz["learners"], quiz["attempts"], quiz["passed"], quiz["average_score"]) == (
        2,
        3,
        2,
        70,
    )
    assert d["stalled_count"] == 2
    assert [s["lessons_done"] for s in d["stalled"]] == [0, 1], "longest idle first"
    weeks = d["weekly_enrolments"]
    assert len(weeks) == 12 and sum(w["count"] for w in weeks) == 4, "12 weeks reach back 40 days"
    assert weeks == sorted(weeks, key=lambda w: w["week"]), "oldest week first"


@pytest.mark.django_db
def test_only_the_instructor_sees_analytics(setup):
    _, course = setup
    url = f"/api/courses/{course.slug}/analytics/"
    assert client_for(UserFactory()).get(url).status_code == 403
    assert client_for(UserFactory(role="admin")).get(url).status_code == 200


@pytest.mark.django_db
def test_empty_course(db):
    course = CourseFactory()
    d = client_for(course.instructor).get(f"/api/courses/{course.slug}/analytics/").data
    assert (d["enrolled"], d["completion_rate"], d["average_days_to_complete"]) == (0, 0, None)
    assert d["lessons"] == [] and d["stalled"] == [] and len(d["weekly_enrolments"]) == 12
