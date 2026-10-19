"""Subscribers that turn domain events into notifications.

Event names are plain strings: this context sits below learning in the layer order, so it
reads the payload and never imports learning code. Publishers put what a notification shows
(titles, slugs, names) in the payload.
"""

from datetime import datetime

from apps.core.events import subscribe

from .models import Notification
from .services import notify

Kind = Notification.Kind


def _when(iso: str) -> str:
    # The server cannot know the reader's time zone; the app shows local time, email shows UTC.
    return datetime.fromisoformat(iso).strftime("%d %b %Y, %H:%M UTC")


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


@subscribe("community.membership_requested")
def on_membership_requested(
    *, group_name, group_slug, requester_id, requester_name, manager_ids, **_
):
    for manager_id in manager_ids:
        notify(
            manager_id,
            Kind.GROUP_REQUEST,
            f"{requester_name} asked to join {group_name}",
            url=f"/groups/{group_slug}",
            actor_id=requester_id,
        )


@subscribe("community.membership_approved")
def on_membership_approved(*, group_name, group_slug, member_id, approver_id, **_):
    notify(
        member_id,
        Kind.GROUP_APPROVED,
        f"You are now a member of {group_name}",
        url=f"/groups/{group_slug}",
        actor_id=approver_id,
    )


@subscribe("community.event_rsvp")
def on_event_rsvp(*, event_id, event_title, host_id, attendee_id, attendee_name, **_):
    notify(
        host_id,
        Kind.EVENT_RSVP,
        f"{attendee_name} is going to {event_title}",
        url=f"/events/{event_id}",
        actor_id=attendee_id,
    )


@subscribe("careers.application_submitted")
def on_application_submitted(*, job_id, job_title, applicant_id, applicant_name, team_ids, **_):
    for member_id in team_ids:
        notify(
            member_id,
            Kind.APPLICATION_RECEIVED,
            f"{applicant_name} applied to {job_title}",
            url=f"/jobs/{job_id}/applications",
            actor_id=applicant_id,
        )


@subscribe("careers.application_status_changed")
def on_application_status_changed(*, applicant_id, job_title, company_name, status_label, **_):
    notify(
        applicant_id,
        Kind.APPLICATION_UPDATE,
        f"{company_name}: your application for {job_title} is now “{status_label}”",
        url="/applications",
    )


@subscribe("network.recommendation_requested")
def on_recommendation_requested(
    *, requester_id, requester_name, requester_username, recipient_id, message, **_
):
    notify(
        recipient_id,
        Kind.RECOMMENDATION_REQUEST,
        f"{requester_name} asked you for a recommendation",
        body=message,
        url=f"/u/{requester_username}#recommend",
        actor_id=requester_id,
    )


@subscribe("network.recommendation_written")
def on_recommendation_written(*, author_id, author_name, recipient_id, **_):
    notify(
        recipient_id,
        Kind.RECOMMENDATION,
        f"{author_name} wrote you a recommendation",
        body="Read it and choose whether it shows on your profile.",
        url="/me#recommendations",
        actor_id=author_id,
    )


@subscribe("profiles.achievement_earned")
def on_achievement_earned(*, user_id, title, **_):
    notify(user_id, Kind.ACHIEVEMENT, f"New badge: {title}", url="/me")


@subscribe("careers.interview_scheduled")
def on_interview_scheduled(*, applicant_id, job_title, company_name, starts_at, rescheduled, **_):
    verb = "moved your interview" if rescheduled else "invited you to an interview"
    notify(
        applicant_id,
        Kind.INTERVIEW,
        f"{company_name} {verb} for {job_title}",
        body=f"{_when(starts_at)}. Confirm or decline in the app.",
        url="/applications",
    )


@subscribe("careers.interview_cancelled")
def on_interview_cancelled(*, applicant_id, job_title, company_name, starts_at, **_):
    notify(
        applicant_id,
        Kind.INTERVIEW,
        f"{company_name} cancelled your interview for {job_title}",
        body=f"It was set for {_when(starts_at)}.",
        url="/applications",
    )


@subscribe("careers.interview_responded")
def on_interview_responded(
    *, applicant_id, applicant_name, job_id, job_title, accepted, team_ids, **_
):
    answer = "confirmed" if accepted else "declined"
    for member_id in team_ids:
        notify(
            member_id,
            Kind.INTERVIEW_REPLY,
            f"{applicant_name} {answer} the interview for {job_title}",
            url=f"/jobs/{job_id}/applications",
            actor_id=applicant_id,
        )


@subscribe("community.post_shared")
def on_post_shared(*, share_id, author_id, sharer_id, sharer_name, **_):
    notify(
        author_id,
        Kind.POST_SHARED,
        f"{sharer_name} shared your post",
        url=f"/posts/{share_id}",
        actor_id=sharer_id,
    )
