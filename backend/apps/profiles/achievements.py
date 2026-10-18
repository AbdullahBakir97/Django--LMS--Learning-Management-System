"""Badges, awarded from domain events. Event names are strings: the publishers sit above us."""

from apps.core import events
from apps.core.events import subscribe

from . import events as names
from .models import Achievement

Code = Achievement.Code


def award(user_id: int, code: str) -> Achievement | None:
    achievement, created = Achievement.objects.get_or_create(user_id=user_id, code=code)
    if not created:
        return None
    events.publish(names.ACHIEVEMENT_EARNED, user_id=user_id, code=code, title=Code(code).label)
    return achievement


@subscribe("learning.course_completed")
def on_course_completed(*, student_id, completed_count=1, **_):
    award(student_id, Code.FIRST_COURSE)
    if completed_count >= 5:
        award(student_id, Code.FIVE_COURSES)


@subscribe("learning.course_published")
def on_course_published(*, instructor_id, **_):
    award(instructor_id, Code.FIRST_PUBLISHED)


@subscribe(names.SKILL_ENDORSED)
def on_skill_endorsed(*, recipient_id, **_):
    award(recipient_id, Code.FIRST_ENDORSEMENT)


@subscribe("network.connection_accepted")
def on_connection_accepted(*, connection_counts=None, **_):
    for user_id, count in (connection_counts or {}).items():
        if count >= 10:
            award(int(user_id), Code.TEN_CONNECTIONS)


@subscribe("network.recommendation_published")
def on_recommendation_published(*, recipient_id, **_):
    award(recipient_id, Code.RECOMMENDED)
