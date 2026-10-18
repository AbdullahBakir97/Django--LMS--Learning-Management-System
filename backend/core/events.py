"""In-process domain events. Contexts publish after commit; lower layers subscribe.

@subscribe("learning.course_published")
def notify(course_id, **_): ...

publish("learning.course_published", course_id=course.id)
"""

import logging
from collections import defaultdict
from collections.abc import Callable

from django.db import transaction

logger = logging.getLogger(__name__)
_subscribers: dict[str, list[Callable]] = defaultdict(list)


def subscribe(name: str):
    def decorator(handler: Callable):
        _subscribers[name].append(handler)
        return handler

    return decorator


def publish(name: str, **payload):
    transaction.on_commit(lambda: _dispatch(name, payload))


def _dispatch(name: str, payload: dict):
    for handler in _subscribers[name]:
        try:
            handler(**payload)
        except Exception:
            logger.exception("event handler failed", extra={"event": name, "handler": handler})
