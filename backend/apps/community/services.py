"""Writes with rules. Every function takes the acting user first."""

import io

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageOps
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core import events

from . import events as names
from .models import Attendance, Event, EventFeedback, Group, Membership, Post, PostImage
from .selectors import is_member, membership

Role, Status = Membership.Role, Membership.Status


def _name(user) -> str:
    return user.get_full_name() or user.username


def _require_manager(actor, group):
    m = membership(actor, group)
    if not (m and m.can_manage) and actor.role != "admin":
        raise PermissionDenied("Only the group's owner or admins can do this.")


@transaction.atomic
def create_group(actor, **fields) -> Group:
    group = Group.objects.create(owner=actor, **fields)
    Membership.objects.create(group=group, user=actor, role=Role.OWNER)
    return group


def update_group(actor, group: Group, **fields) -> Group:
    _require_manager(actor, group)
    for key, value in fields.items():
        setattr(group, key, value)
    group.save()
    return group


def delete_group(actor, group: Group) -> None:
    if group.owner_id != actor.id and actor.role != "admin":
        raise PermissionDenied("Only the owner can delete a group.")
    group.delete()


def join(actor, group: Group) -> Membership:
    """Public groups admit at once; private groups queue a request for the managers."""
    existing = membership(actor, group)
    if existing:
        return existing
    private = group.privacy == Group.Privacy.PRIVATE
    m = Membership.objects.create(
        group=group, user=actor, status=Status.PENDING if private else Status.ACTIVE
    )
    if private:
        managers = list(
            Membership.objects.filter(
                group=group, status=Status.ACTIVE, role__in=[Role.OWNER, Role.ADMIN]
            ).values_list("user_id", flat=True)
        )
        events.publish(
            names.MEMBERSHIP_REQUESTED,
            group_name=group.name,
            group_slug=group.slug,
            requester_id=actor.id,
            requester_name=_name(actor),
            manager_ids=managers,
        )
    return m


def leave(actor, group: Group) -> None:
    if group.owner_id == actor.id:
        raise ValidationError("The owner cannot leave. Transfer or delete the group instead.")
    Membership.objects.filter(group=group, user=actor).delete()


def approve(actor, group: Group, user_id) -> Membership:
    _require_manager(actor, group)
    m = Membership.objects.filter(group=group, user_id=user_id, status=Status.PENDING).first()
    if m is None:
        raise ValidationError("No pending request from this person.")
    m.status = Status.ACTIVE
    m.save(update_fields=["status", "updated_at"])
    events.publish(
        names.MEMBERSHIP_APPROVED,
        group_name=group.name,
        group_slug=group.slug,
        member_id=user_id,
        approver_id=actor.id,
    )
    return m


def remove_member(actor, group: Group, user_id) -> None:
    """Managers decline requests or remove members. Nobody removes the owner."""
    _require_manager(actor, group)
    if user_id == group.owner_id:
        raise ValidationError("The owner cannot be removed.")
    Membership.objects.filter(group=group, user_id=user_id).delete()


def set_role(actor, group: Group, user_id, role: str) -> Membership:
    if group.owner_id != actor.id:
        raise PermissionDenied("Only the owner can change roles.")
    if role not in (Role.ADMIN, Role.MEMBER) or user_id == group.owner_id:
        raise ValidationError("Choose admin or member for someone other than the owner.")
    m = Membership.objects.filter(group=group, user_id=user_id, status=Status.ACTIVE).first()
    if m is None:
        raise ValidationError("This person is not a member.")
    m.role = role
    m.save(update_fields=["role", "updated_at"])
    return m


MAX_IMAGES = 4
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_SIDE = 2000


def _clean_image(upload) -> tuple[ContentFile, int, int]:
    """Re-encode: drops EXIF (phone photos carry GPS), turns it upright, and caps its size."""
    if upload.size > MAX_IMAGE_BYTES:
        raise ValidationError({"images": "Each image must be 8 MB or smaller."})
    try:
        with Image.open(upload) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
            out = io.BytesIO()
            img.save(out, "JPEG", quality=85, optimize=True)
    except (OSError, Image.DecompressionBombError):
        raise ValidationError({"images": "That file is not an image we can read."}) from None
    return ContentFile(out.getvalue(), name="image.jpg"), img.width, img.height


@transaction.atomic
def create_post(actor, body: str, group: Group | None = None, images=()) -> Post:
    if group is not None and not is_member(actor, group):
        raise PermissionDenied("Join the group to post in it.")
    if len(images) > MAX_IMAGES:
        raise ValidationError({"images": f"Up to {MAX_IMAGES} images per post."})
    if not body.strip() and not images:
        raise ValidationError({"body": "Write something or add an image."})
    cleaned = [_clean_image(upload) for upload in images]  # all checked before anything is saved
    post = Post.objects.create(author=actor, body=body, group=group)
    for position, (file, width, height) in enumerate(cleaned):
        PostImage.objects.create(
            post=post, image=file, width=width, height=height, position=position
        )
    return post


def share_post(actor, post: Post, body: str = "") -> Post:
    """Share to your own profile. Only posts anyone may read can travel."""
    original = post.shared_from or post
    if original.group_id and original.group.privacy != Group.Privacy.PUBLIC:
        raise PermissionDenied("Posts in private groups stay in the group.")
    share = Post.objects.create(author=actor, body=body, shared_from=original)
    if original.author_id != actor.id:
        events.publish(
            names.POST_SHARED,
            post_id=original.id,
            share_id=share.id,
            author_id=original.author_id,
            sharer_id=actor.id,
            sharer_name=_name(actor),
        )
    return share


def edit_post(actor, post: Post, body: str) -> Post:
    if post.author_id != actor.id:
        raise PermissionDenied("Only the author can edit a post.")
    post.body = body
    post.edited_at = timezone.now()
    post.save(update_fields=["body", "edited_at", "updated_at"])
    return post


def can_moderate_post(actor, post: Post) -> bool:
    if post.author_id == actor.id or actor.role == "admin":
        return True
    m = membership(actor, post.group) if post.group_id else None
    return bool(m and m.can_manage)


def delete_post(actor, post: Post) -> None:
    if not can_moderate_post(actor, post):
        raise PermissionDenied("You cannot delete this post.")
    post.delete()


def create_event(actor, group: Group | None = None, **fields) -> Event:
    if group is not None:
        _require_manager(actor, group)
    if fields["ends_at"] <= fields["starts_at"]:
        raise ValidationError({"ends_at": "An event ends after it starts."})
    return Event.objects.create(host=actor, group=group, **fields)


def update_event(actor, event: Event, **fields) -> Event:
    if event.host_id != actor.id and actor.role != "admin":
        raise PermissionDenied("Only the host can change this event.")
    for key, value in fields.items():
        setattr(event, key, value)
    if event.ends_at <= event.starts_at:
        raise ValidationError({"ends_at": "An event ends after it starts."})
    event.save()
    return event


def delete_event(actor, event: Event) -> None:
    if event.host_id != actor.id and actor.role != "admin":
        raise PermissionDenied("Only the host can cancel this event.")
    event.delete()


@transaction.atomic
def rsvp(actor, event: Event, status: str) -> Attendance:
    if event.ends_at <= timezone.now():
        raise ValidationError("This event is over.")
    Event.objects.select_for_update().filter(pk=event.pk).first()  # serialise capacity checks
    if status == Attendance.Status.GOING and event.capacity is not None:
        going = event.attendances.filter(status=Attendance.Status.GOING).exclude(user=actor).count()
        if going >= event.capacity:
            raise ValidationError("This event is full.")
    before = Attendance.objects.filter(event=event, user=actor).values_list("status", flat=True)
    was = before.first()
    attendance, _ = Attendance.objects.update_or_create(
        event=event, user=actor, defaults={"status": status}
    )
    if status == Attendance.Status.GOING and was != status and actor.id != event.host_id:
        events.publish(
            names.EVENT_RSVP,
            event_id=event.id,
            event_title=event.title,
            host_id=event.host_id,
            attendee_id=actor.id,
            attendee_name=_name(actor),
        )
    return attendance


def cancel_rsvp(actor, event: Event) -> None:
    Attendance.objects.filter(event=event, user=actor).delete()


def give_feedback(actor, event: Event, rating: int, comment: str = "") -> EventFeedback:
    if event.ends_at > timezone.now():
        raise ValidationError("Feedback opens when the event is over.")
    went = Attendance.objects.filter(event=event, user=actor, status=Attendance.Status.GOING)
    if not went.exists():
        raise PermissionDenied("Only people who went can rate an event.")
    feedback, _ = EventFeedback.objects.update_or_create(
        event=event, user=actor, defaults={"rating": rating, "comment": comment}
    )
    return feedback
