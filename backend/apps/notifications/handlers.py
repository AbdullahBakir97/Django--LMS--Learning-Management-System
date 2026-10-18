"""Subscribers that turn domain events into notifications.

Event names are plain strings: this context sits below learning in the layer order, so it
reads the payload and never imports learning code. Publishers put what a notification shows
(titles, slugs, names) in the payload.
"""

from apps.core.events import subscribe

from .models import Notification
from .services import notify

Kind = Notification.Kind


@subscribe("learning.enrolled")
def on_enrolled(*, instructor_id, student_id, student_name, course_title, course_slug, **_):
    notify(
        instructor_id,
        Kind.ENROLMENT,
        f"{student_name} enrolled in {course_title}",
        url=f"/teach/{course_slug}",
        actor_id=student_id,
    )


@subscribe("learning.course_completed")
def on_course_completed(*, student_id, course_title, certificate_code, **_):
    notify(
        student_id,
        Kind.COURSE_COMPLETED,
        f"You completed {course_title}",
        body="Your certificate is ready. Anyone with the link can verify it.",
        url=f"/certificates/{certificate_code}",
    )


@subscribe("profiles.skill_endorsed")
def on_skill_endorsed(*, recipient_id, actor_id, actor_name, skill_name, **_):
    notify(
        recipient_id,
        Kind.ENDORSEMENT,
        f"{actor_name} endorsed you for {skill_name}",
        url="/me",
        actor_id=actor_id,
    )
