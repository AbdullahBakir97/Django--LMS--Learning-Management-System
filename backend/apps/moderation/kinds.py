"""What can be reported, and how each kind is shown to staff and removed.

This app sits above every other one, so it may call their selectors and services.
"""

from collections.abc import Callable
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.http import Http404

from apps.community import selectors as community
from apps.community import services as community_services
from apps.community.models import Post
from apps.engagement import registry
from apps.engagement import services as engagement
from apps.engagement.models import Comment

User = get_user_model()


@dataclass(frozen=True)
class Kind:
    fetch: Callable  # (pk) -> obj | None
    can_view: Callable  # (user, obj) -> bool
    author_id: Callable  # (obj) -> int: nobody reports themselves
    preview: Callable  # (obj) -> dict
    remove: Callable  # (moderator, obj) -> None


def _excerpt(text: str, n: int = 280) -> str:
    return text if len(text) <= n else f"{text[:n]}…"


def _comment_target(comment):
    target = registry.get(comment.target_type)
    return target, target.model.objects.filter(pk=comment.target_id).first()


def _can_view_comment(user, comment) -> bool:
    target, obj = _comment_target(comment)
    return comment.deleted_at is None and obj is not None and target.can_view(user, obj)


def _remove_comment(moderator, comment) -> None:
    target, obj = _comment_target(comment)
    engagement.delete_comment(moderator, comment, target, obj)


def _comment_preview(comment) -> dict:
    target, obj = _comment_target(comment)
    return {
        "title": f"Comment by {_name(comment.author)}",
        "excerpt": _excerpt(comment.body) or "(already removed)",
        "url": target.url(obj) if obj else "",
        "author": comment.author.username,
    }


def _deactivate(moderator, user) -> None:
    # They can no longer sign in; what they wrote stays until removed on its own.
    user.is_active = False
    user.save(update_fields=["is_active"])


def _name(user) -> str:
    return user.get_full_name() or user.username


KINDS: dict[str, Kind] = {
    "post": Kind(
        fetch=lambda pk: Post.objects.select_related("author", "group").filter(pk=pk).first(),
        can_view=community.can_view_post,
        author_id=lambda p: p.author_id,
        preview=lambda p: {
            "title": f"Post by {_name(p.author)}",
            "excerpt": _excerpt(p.body),
            "url": f"/posts/{p.pk}",
            "author": p.author.username,
        },
        remove=community_services.delete_post,
    ),
    "comment": Kind(
        fetch=lambda pk: Comment.objects.select_related("author").filter(pk=pk).first(),
        can_view=_can_view_comment,
        author_id=lambda c: c.author_id,
        preview=_comment_preview,
        remove=_remove_comment,
    ),
    "user": Kind(
        fetch=lambda pk: (
            User.objects.select_related("profile").filter(pk=pk, is_active=True).first()
        ),
        can_view=lambda viewer, u: True,
        author_id=lambda u: u.pk,
        preview=lambda u: {
            "title": _name(u),
            "excerpt": u.profile.headline,
            "url": f"/u/{u.username}",
            "author": u.username,
        },
        remove=_deactivate,
    ),
}


def visible(kind: str, pk, user):
    """The reported object if it exists and the user may see it; 404 otherwise."""
    spec = KINDS.get(kind)
    obj = spec.fetch(pk) if spec else None
    if obj is None or not spec.can_view(user, obj):
        raise Http404("Not found.")
    return spec, obj
