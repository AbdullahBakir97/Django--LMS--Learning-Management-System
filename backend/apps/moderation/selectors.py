from collections import defaultdict

from .kinds import KINDS
from .models import Report

QUEUE_LIMIT = 100


def queue(status: str = Report.Status.OPEN) -> list[dict]:
    """Reports grouped by what they are about, oldest first."""
    # shortcut: groups in Python and previews one object per group; fine for a moderation
    # queue of hundreds, move the grouping into SQL if it grows into thousands.
    reports = Report.objects.filter(status=status).select_related("reporter", "resolved_by")
    groups: dict[tuple[str, int], list[Report]] = defaultdict(list)
    for r in reports.order_by("created_at"):
        groups[(r.kind, r.object_id)].append(r)
    out = []
    for (kind, object_id), rows in list(groups.items())[:QUEUE_LIMIT]:
        obj = KINDS[kind].fetch(object_id)
        reasons: dict[str, int] = defaultdict(int)
        for r in rows:
            reasons[r.reason] += 1
        out.append(
            {
                "kind": kind,
                "object_id": object_id,
                "exists": obj is not None,
                "preview": KINDS[kind].preview(obj) if obj else None,
                "report_count": len(rows),
                "reasons": dict(reasons),
                "reports": rows,
                "first_reported_at": rows[0].created_at,
            }
        )
    return out
