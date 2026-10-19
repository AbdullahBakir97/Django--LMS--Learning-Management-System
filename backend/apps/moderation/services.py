"""Writes with rules. Every function takes the acting user first."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core import events

from .kinds import KINDS, visible
from .models import Report

REPORT_RESOLVED = "moderation.report_resolved"


def report(actor, kind: str, object_id: int, reason: str, details: str = "") -> tuple[Report, bool]:
    spec, obj = visible(kind, object_id, actor)
    if spec.author_id(obj) == actor.id:
        raise ValidationError("You cannot report yourself or your own content.")
    # One report per person and thing: asking again changes nothing and tells nobody twice.
    return Report.objects.get_or_create(
        reporter=actor,
        kind=kind,
        object_id=object_id,
        defaults={"reason": reason, "details": details},
    )


@transaction.atomic
def resolve(moderator, kind: str, object_id: int, remove: bool, note: str = "") -> int:
    """Close every open report on one thing, removing it first when asked. Returns how many."""
    if moderator.role != "admin":
        raise PermissionDenied("Only moderators resolve reports.")
    open_reports = Report.objects.select_for_update().filter(
        kind=kind, object_id=object_id, status=Report.Status.OPEN
    )
    reporter_ids = list(open_reports.values_list("reporter_id", flat=True))
    if not reporter_ids:
        raise ValidationError("Nothing open to resolve here.")
    if remove:
        obj = KINDS[kind].fetch(object_id)
        if obj is not None:
            KINDS[kind].remove(moderator, obj)
    status = Report.Status.REMOVED if remove else Report.Status.DISMISSED
    count = open_reports.update(
        status=status, resolved_by=moderator, resolved_at=timezone.now(), note=note
    )
    events.publish(REPORT_RESOLVED, reporter_ids=reporter_ids, removed=remove)
    return count
