"""Numbers an instructor needs about one course. Read-only; a handful of grouped queries."""

from datetime import timedelta

from django.db.models import Avg, Count, F, Max, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce, Greatest, TruncWeek
from django.utils import timezone

from .models import Course, Enrollment, LessonProgress, QuizAttempt

WEEKS = 12
STALLED_AFTER = timedelta(days=14)
STALLED_SHOWN = 10


def _weekly(course: Course, now) -> list[dict]:
    """Enrolments per week for the last WEEKS weeks, empty weeks included."""
    this_week = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start = this_week - timedelta(weeks=WEEKS - 1)
    counts = dict(
        Enrollment.objects.filter(course=course, created_at__gte=start)
        .annotate(week=TruncWeek("created_at"))
        .values_list("week")
        .annotate(n=Count("id"))
        .values_list("week", "n")
    )
    by_date = {week.date(): n for week, n in counts.items()}
    return [
        {
            "week": (start + timedelta(weeks=i)).date(),
            "count": by_date.get((start + timedelta(weeks=i)).date(), 0),
        }
        for i in range(WEEKS)
    ]


def course_analytics(course: Course) -> dict:
    now = timezone.now()
    enrolments = Enrollment.objects.filter(course=course)
    totals = enrolments.aggregate(
        enrolled=Count("id"),
        completed=Count("id", filter=Q(status=Enrollment.Status.COMPLETED)),
        avg_duration=Avg(F("completed_at") - F("created_at"), filter=Q(completed_at__isnull=False)),
    )
    enrolled = totals["enrolled"]

    # Where learners stop: how many finished each lesson, in course order.
    done = dict(
        LessonProgress.objects.filter(enrollment__course=course)
        .values_list("lesson_id")
        .annotate(n=Count("id"))
        .values_list("lesson_id", "n")
    )
    lessons = [
        {
            "id": lesson.id,
            "title": lesson.title,
            "order": lesson.order,
            "completed": done.get(lesson.id, 0),
        }
        for lesson in course.lessons.order_by("order")
    ]

    quizzes = [
        {
            "lesson_id": row["quiz__lesson_id"],
            "title": row["quiz__title"],
            "learners": row["learners"],
            "attempts": row["attempts"],
            "passed": row["passed"],
            "average_score": round(row["avg_score"] or 0),
        }
        for row in QuizAttempt.objects.filter(quiz__lesson__course=course)
        .values("quiz_id", "quiz__lesson_id", "quiz__title", "quiz__lesson__order")
        .annotate(
            learners=Count("enrollment", distinct=True),
            attempts=Count("id"),
            passed=Count("enrollment", filter=Q(passed=True), distinct=True),
            avg_score=Avg("score"),
        )
        .order_by("quiz__lesson__order")
    ]

    # Stalled: still active, nothing done for STALLED_AFTER. Last activity is the latest of
    # enrolling, finishing a lesson and attempting a quiz.
    last_lesson = (
        LessonProgress.objects.filter(enrollment=OuterRef("pk"))
        .values("enrollment")
        .annotate(t=Max("created_at"))
        .values("t")
    )
    last_quiz = (
        QuizAttempt.objects.filter(enrollment=OuterRef("pk"))
        .values("enrollment")
        .annotate(t=Max("created_at"))
        .values("t")
    )
    active = enrolments.filter(status=Enrollment.Status.ACTIVE).annotate(
        last_active=Greatest(
            "created_at",
            Coalesce(Subquery(last_lesson), "created_at"),
            Coalesce(Subquery(last_quiz), "created_at"),
        ),
        lessons_done=Count("lesson_progress", distinct=True),
    )
    stalled = active.filter(last_active__lt=now - STALLED_AFTER)
    duration = totals["avg_duration"]
    return {
        "enrolled": enrolled,
        "active": enrolled - totals["completed"],
        "completed": totals["completed"],
        "completion_rate": round(100 * totals["completed"] / enrolled) if enrolled else 0,
        "average_days_to_complete": round(duration.total_seconds() / 86400, 1)
        if duration
        else None,
        "lesson_count": len(lessons),
        "weekly_enrolments": _weekly(course, now),
        "lessons": lessons,
        "quizzes": quizzes,
        "stalled_count": stalled.count(),
        "stalled": [
            {
                "username": e.student.username,
                "name": e.student.get_full_name() or e.student.username,
                "lessons_done": e.lessons_done,
                "last_active": e.last_active,
            }
            for e in stalled.select_related("student").order_by("last_active")[:STALLED_SHOWN]
        ],
    }
