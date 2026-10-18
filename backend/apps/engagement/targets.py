"""Engagement's own target: reactions on comments. A comment is visible if its target is."""

from . import registry
from .models import Comment


def _comment_visible(user, comment) -> bool:
    if comment.deleted_at is not None:
        return False
    target = registry.get(comment.target_type)
    obj = target.model.objects.filter(pk=comment.target_id).first()
    return obj is not None and target.can_view(user, obj)


def _comment_url(comment) -> str:
    target = registry.get(comment.target_type)
    obj = target.model.objects.filter(pk=comment.target_id).first()
    return f"{target.url(obj)}#comment-{comment.pk}" if obj else ""


registry.register(
    "comment",
    Comment,
    can_view=_comment_visible,
    owner_id=lambda c: c.author_id,
    url=_comment_url,
    title=lambda c: c.body[:60],
    commentable=False,
)
