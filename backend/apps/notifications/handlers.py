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


@subscribe("network.followed")
def on_followed(*, follower_id, follower_name, follower_username, following_id, **_):
    notify(
        following_id,
        Kind.FOLLOW,
        f"{follower_name} started following you",
        url=f"/u/{follower_username}",
        actor_id=follower_id,
    )


@subscribe("network.connection_requested")
def on_connection_requested(*, requester_id, requester_name, addressee_id, **_):
    notify(
        addressee_id,
        Kind.CONNECTION_REQUEST,
        f"{requester_name} wants to connect",
        url="/network",
        actor_id=requester_id,
    )


@subscribe("network.connection_accepted")
def on_connection_accepted(*, requester_id, addressee_id, addressee_name, addressee_username, **_):
    notify(
        requester_id,
        Kind.CONNECTION_ACCEPTED,
        f"{addressee_name} accepted your connection request",
        url=f"/u/{addressee_username}",
        actor_id=addressee_id,
    )


@subscribe("engagement.commented")
def on_commented(*, author_id, author_name, owner_id, parent_author_id, title, url, **_):
    if parent_author_id:
        notify(
            parent_author_id,
            Kind.REPLY,
            f"{author_name} replied to your comment on {title}",
            url=url,
            actor_id=author_id,
        )
    if owner_id and owner_id != parent_author_id:
        notify(
            owner_id,
            Kind.COMMENT,
            f"{author_name} commented on {title}",
            url=url,
            actor_id=author_id,
        )
