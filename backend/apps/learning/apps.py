from django.apps import AppConfig


class LearningConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.learning"

    def ready(self):
        from apps.engagement import registry

        from . import selectors
        from .models import Lesson

        def can_view(user, lesson):
            course = lesson.course
            visible = course.status == course.Status.PUBLISHED or course.instructor_id == user.id
            enrollment = selectors.enrollment_for(user, course)
            return visible and selectors.can_view_lesson(user, lesson, enrollment)

        registry.register(
            "lesson",
            Lesson,
            can_view=can_view,
            owner_id=lambda lesson: lesson.course.instructor_id,
            url=lambda lesson: f"/courses/{lesson.course.slug}/lessons/{lesson.pk}",
            title=lambda lesson: lesson.title,
        )
