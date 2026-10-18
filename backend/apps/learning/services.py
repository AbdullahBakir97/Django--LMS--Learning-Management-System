"""Writes with rules. The acting user is always the first argument."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core import events
from apps.core.exceptions import PaymentRequired

from . import events as names
from .models import Certificate, Course, Enrollment, Lesson, LessonProgress, Quiz, QuizAttempt
from .tasks import render_certificate_pdf


def publish_course(actor, course: Course) -> Course:
    if not course.lessons.exists():
        raise ValidationError("Add at least one lesson before publishing.")
    if not course.is_published:
        course.status = Course.Status.PUBLISHED
        course.published_at = timezone.now()
        course.save(update_fields=["status", "published_at", "updated_at"])
        events.publish(names.COURSE_PUBLISHED, course_id=course.id, instructor_id=actor.id)
    return course


def check_can_enroll(actor, course: Course) -> None:
    if not course.is_published:
        raise ValidationError("This course is not published.")
    if course.instructor_id == actor.id:
        raise ValidationError("You teach this course.")
    if Enrollment.objects.filter(course=course, student=actor).exists():
        raise ValidationError("You are already enrolled.")
    missing = course.prerequisites.exclude(
        enrollments__student=actor, enrollments__status=Enrollment.Status.COMPLETED
    )
    if missing.exists():
        raise ValidationError({"prerequisites": [f"Complete “{c.title}” first." for c in missing]})


def enroll(actor, course: Course, *, paid: bool = False) -> Enrollment:
    """`paid=True` is for payments, after checkout: the rules were checked before payment."""
    if not paid:
        check_can_enroll(actor, course)
        if course.is_paid:
            raise PaymentRequired()
    enrollment, created = Enrollment.objects.get_or_create(course=course, student=actor)
    if created:
        events.publish(
            names.ENROLLED,
            enrollment_id=enrollment.id,
            course_id=course.id,
            course_title=course.title,
            course_slug=course.slug,
            instructor_id=course.instructor_id,
            student_id=actor.id,
            student_name=actor.get_full_name() or actor.username,
        )
    return enrollment


def unenroll(student, course: Course) -> None:
    """Payments, after a refund: access ends, and progress and any certificate go with it."""
    Enrollment.objects.filter(course=course, student=student).delete()


def _enrollment_or_403(actor, course: Course) -> Enrollment:
    enrollment = Enrollment.objects.filter(course=course, student=actor).first()
    if enrollment is None:
        raise PermissionDenied("Enrol in this course first.")
    return enrollment


@transaction.atomic
def complete_lesson(actor, lesson: Lesson) -> Enrollment:
    enrollment = _enrollment_or_403(actor, lesson.course)
    LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    _check_completion(enrollment)
    return enrollment


@transaction.atomic
def submit_quiz(actor, quiz: Quiz, answers: dict[int, int]) -> QuizAttempt:
    enrollment = _enrollment_or_403(actor, quiz.lesson.course)
    questions = list(quiz.questions.prefetch_related("choices"))
    if not questions:
        raise ValidationError("This quiz has no questions yet.")
    correct = 0
    for question in questions:
        chosen = answers.get(question.id)
        if any(c.id == chosen and c.is_correct for c in question.choices.all()):
            correct += 1
    score = round(100 * correct / len(questions))
    attempt = QuizAttempt.objects.create(
        enrollment=enrollment,
        quiz=quiz,
        score=score,
        passed=score >= quiz.pass_score,
        answers={str(k): v for k, v in answers.items()},
    )
    if attempt.passed:
        LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=quiz.lesson)
        _check_completion(enrollment)
    return attempt


def _check_completion(enrollment: Enrollment) -> None:
    """Every lesson done and every quiz passed → completed, certificate issued."""
    if enrollment.status == Enrollment.Status.COMPLETED:
        return
    course = enrollment.course
    lesson_ids = set(course.lessons.values_list("id", flat=True))
    done = set(enrollment.lesson_progress.values_list("lesson_id", flat=True))
    if lesson_ids - done:
        return
    quiz_ids = set(Quiz.objects.filter(lesson__course=course).values_list("id", flat=True))
    passed = set(enrollment.quiz_attempts.filter(passed=True).values_list("quiz_id", flat=True))
    if quiz_ids - passed:
        return
    enrollment.status = Enrollment.Status.COMPLETED
    enrollment.completed_at = timezone.now()
    enrollment.save(update_fields=["status", "completed_at", "updated_at"])
    certificate = Certificate.objects.create(enrollment=enrollment)
    transaction.on_commit(lambda: render_certificate_pdf.delay(certificate.id))
    events.publish(
        names.COURSE_COMPLETED,
        enrollment_id=enrollment.id,
        course_id=course.id,
        course_title=course.title,
        student_id=enrollment.student_id,
        certificate_code=str(certificate.code),
        completed_count=Enrollment.objects.filter(
            student_id=enrollment.student_id, status=Enrollment.Status.COMPLETED
        ).count(),
    )
