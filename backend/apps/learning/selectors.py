from django.db.models import OuterRef, Prefetch, Q

from apps.core.stats import count_of

from .models import Course, Enrollment, Lesson, Question


def visible_courses(user):
    """Published courses, plus the drafts the user teaches."""
    # Subqueries, not two Counts: joining lessons and enrolments multiplies the rows.
    qs = Course.objects.select_related("instructor").annotate(
        lesson_count=count_of(Lesson.objects.filter(course=OuterRef("pk"))),
        enrollment_count=count_of(Enrollment.objects.filter(course=OuterRef("pk"))),
    )
    return qs.filter(Q(status=Course.Status.PUBLISHED) | Q(instructor=user))


def course_with_lessons(user):
    return visible_courses(user).prefetch_related(
        Prefetch("lessons", queryset=Lesson.objects.select_related("quiz")), "prerequisites"
    )


def enrollment_for(user, course):
    return (
        Enrollment.objects.filter(student=user, course=course)
        .prefetch_related("lesson_progress", "quiz_attempts")
        .first()
    )


def quiz_questions(quiz):
    return Question.objects.filter(quiz=quiz).prefetch_related("choices")


def can_view_lesson(user, lesson, enrollment) -> bool:
    return (
        lesson.is_free_preview
        or enrollment is not None
        or lesson.course.instructor_id == user.id
        or user.role == "admin"
    )
