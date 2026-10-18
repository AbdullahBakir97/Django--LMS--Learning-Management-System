"""What can be commented on or reacted to.

Engagement sits below the product contexts, so it cannot import them. Instead each product
context registers its models here from its AppConfig.ready():

    registry.register("lesson", Lesson, can_view=..., owner_id=..., url=..., title=...)

The API then addresses a target as /api/engagement/<key>/<id>/... and never needs to know
what a lesson is.
"""

from collections.abc import Callable
from dataclasses import dataclass

from django.http import Http404


@dataclass(frozen=True)
class Target:
    key: str
    model: type
    can_view: Callable  # (user, obj) -> bool
    owner_id: Callable  # (obj) -> int | None; may moderate and is told about new comments
    url: Callable  # (obj) -> str, a path inside the SPA
    title: Callable  # (obj) -> str
    commentable: bool = True


_targets: dict[str, Target] = {}


def register(key: str, model, **behaviour) -> None:
    _targets[key] = Target(key=key, model=model, **behaviour)


def get(key: str) -> Target:
    if key not in _targets:
        raise Http404("Unknown target.")
    return _targets[key]


def resolve(key: str, pk, user):
    """The target object if it exists and the user may see it; 404 otherwise (no existence leak)."""
    target = get(key)
    obj = target.model.objects.filter(pk=pk).first()
    if obj is None or not target.can_view(user, obj):
        raise Http404("Not found.")
    return target, obj
