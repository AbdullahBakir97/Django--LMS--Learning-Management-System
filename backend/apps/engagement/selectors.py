from collections import Counter, defaultdict

from django.db.models import Exists, OuterRef, Prefetch

from .models import Comment, Reaction


def thread(target_type: str, target_id):
    """Top-level comments, oldest first, with their replies. A removed comment stays only as a
    placeholder while it still has live replies."""
    live_replies = Comment.objects.filter(parent=OuterRef("pk"), deleted_at__isnull=True)
    replies = Comment.objects.select_related("author__profile").filter(deleted_at__isnull=True)
    return (
        Comment.objects.filter(target_type=target_type, target_id=target_id, parent=None)
        .annotate(has_live_replies=Exists(live_replies))
        .exclude(deleted_at__isnull=False, has_live_replies=False)
        .select_related("author__profile")
        .prefetch_related(Prefetch("replies", queryset=replies))
    )


def reaction_summary(target_type: str, ids, user) -> dict:
    """{target_id: {"counts": {kind: n}, "mine": kind | None}} for many targets in one query."""
    out = defaultdict(lambda: {"counts": {}, "mine": None})
    counts = defaultdict(Counter)
    for target_id, kind, user_id in Reaction.objects.filter(
        target_type=target_type, target_id__in=list(ids)
    ).values_list("target_id", "kind", "user_id"):
        counts[target_id][kind] += 1
        if user_id == user.id:
            out[target_id]["mine"] = kind
    for target_id, c in counts.items():
        out[target_id]["counts"] = dict(c)
    return out
