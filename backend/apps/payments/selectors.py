from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from .models import Order

RECENT = timedelta(days=30)


def revenue(orders=None) -> list[dict]:
    """Paid orders per currency, biggest first: all time, the last 30 days, and the count.

    Refunded orders are left out, so a refund lowers the totals.
    """
    since = timezone.now() - RECENT
    orders = (orders if orders is not None else Order.objects).filter(status=Order.Status.PAID)
    return list(
        orders.values("currency")
        .annotate(
            total_cents=Sum("paid_cents"),
            recent_cents=Sum("paid_cents", filter=Q(paid_at__gte=since), default=0),
            orders=Count("id"),
        )
        .order_by("-total_cents")
    )
