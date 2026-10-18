"""Writes with rules. Every function takes the acting user first."""

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core import events

from . import events as names
from .models import Comment, Reaction


def add_comment(actor, target, obj, body: str, parent: Comment | None = None) -> Comment:
    if not target.commentable:
        raise ValidationError("This cannot be commented on.")
    if parent is not None and (
        parent.target_type != target.key
        or parent.target_id != obj.pk
        or parent.parent_id is not None
        or parent.deleted_at is not None
    ):
        raise ValidationError({"parent": "Reply to a comment in this thread."})
    comment = Comment.objects.create(
        author=actor, target_type=target.key, target_id=obj.pk, parent=parent, body=body
    )
    events.publish(
        names.COMMENTED,
        comment_id=comment.id,
        author_id=actor.id,
        author_name=actor.get_full_name() or actor.username,
        owner_id=target.owner_id(obj),
        parent_author_id=parent.author_id if parent else None,
        title=target.title(obj),
        url=f"{target.url(obj)}#comment-{comment.id}",
    )
    return comment


def edit_comment(actor, comment: Comment, body: str) -> Comment:
    if comment.author_id != actor.id or comment.deleted_at is not None:
        raise PermissionDenied("Only the author can edit a comment.")
    comment.body = body
    comment.edited_at = timezone.now()
    comment.save(update_fields=["body", "edited_at", "updated_at"])
    return comment


def can_moderate(actor, target, obj) -> bool:
    return target.owner_id(obj) == actor.id or actor.role == "admin"


def delete_comment(actor, comment: Comment, target, obj) -> None:
    """Soft delete: the author, the target's owner (an instructor on their lesson) or an admin."""
    if comment.author_id != actor.id and not can_moderate(actor, target, obj):
        raise PermissionDenied("You cannot remove this comment.")
    comment.body = ""
    comment.deleted_at = timezone.now()
    comment.save(update_fields=["body", "deleted_at", "updated_at"])
    Reaction.objects.filter(target_type="comment", target_id=comment.id).delete()


def react(actor, target_type: str, target_id, kind: str) -> Reaction:
    reaction, _ = Reaction.objects.update_or_create(
        user=actor, target_type=target_type, target_id=target_id, defaults={"kind": kind}
    )
    return reaction


def unreact(actor, target_type: str, target_id) -> None:
    Reaction.objects.filter(user=actor, target_type=target_type, target_id=target_id).delete()
