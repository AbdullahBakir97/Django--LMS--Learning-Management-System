"""Small reporting helpers shared by analytics screens."""

from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.utils import timezone


def weekly_counts(queryset, field: str = "created_at", weeks: int = 12, now=None) -> list[dict]:
    """Rows per week (Monday start) for the last `weeks` weeks, empty weeks included."""
    now = now or timezone.now()
    this_week = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start = this_week - timedelta(weeks=weeks - 1)
    counts = dict(
        queryset.filter(**{f"{field}__gte": start})
        .annotate(week=TruncWeek(field))
        .values_list("week")
        .annotate(n=Count("id"))
        .values_list("week", "n")
    )
    by_date = {week.date(): n for week, n in counts.items()}
    days = [(start + timedelta(weeks=i)).date() for i in range(weeks)]
    return [{"week": day, "count": by_date.get(day, 0)} for day in days]
