from django.db.models import Count, Prefetch, Q

from .models import Course, Enrollment, Lesson, Question


def visible_courses(user):
    """Published courses, plus the drafts the user teaches."""
    qs = Course.objects.select_related("instructor").annotate(
        lesson_count=Count("lessons", distinct=True),
        enrollment_count=Count("enrollments", distinct=True),
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
