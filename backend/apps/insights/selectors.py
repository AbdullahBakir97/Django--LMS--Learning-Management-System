"""The platform at a glance, for admins. Read-only counts across every context; no models."""

from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.accounts.models import User
from apps.careers.models import Job
from apps.community.models import Post
from apps.core.stats import weekly_counts
from apps.learning.models import Course, Enrollment
from apps.moderation.models import Report
from apps.payments.models import Order

RECENT = timedelta(days=30)
TOP_COURSES = 5


def overview() -> dict:
    since = timezone.now() - RECENT
    people = User.objects.filter(is_active=True)
    enrolments = Enrollment.objects.all()
    learning = enrolments.aggregate(
        total=Count("id"),
        recent=Count("id", filter=Q(created_at__gte=since)),
        completed=Count("id", filter=Q(status=Enrollment.Status.COMPLETED)),
    )
    paid = Order.objects.filter(status=Order.Status.PAID)
    top = (
        Course.objects.filter(status=Course.Status.PUBLISHED)
        .annotate(
            recent=Count("enrollments", filter=Q(enrollments__created_at__gte=since)),
            enrolled=Count("enrollments"),
        )
        .filter(enrolled__gt=0)
        .select_related("instructor")
        .order_by("-recent", "-enrolled", "title")[:TOP_COURSES]
    )
    return {
        "people": people.count(),
        "new_people": people.filter(date_joined__gte=since).count(),
        "courses": Course.objects.filter(status=Course.Status.PUBLISHED).count(),
        "enrolments": learning["total"],
        "new_enrolments": learning["recent"],
        "completion_rate": round(100 * learning["completed"] / learning["total"])
        if learning["total"]
        else 0,
        "posts": Post.objects.filter(created_at__gte=since).count(),
        "open_jobs": Job.objects.filter(status=Job.Status.OPEN).count(),
        "open_reports": Report.objects.filter(status=Report.Status.OPEN)
        .values("kind", "object_id")
        .distinct()
        .count(),
        "revenue": list(
            paid.values("currency")
            .annotate(
                total_cents=Sum("amount_cents"),
                recent_cents=Sum("amount_cents", filter=Q(paid_at__gte=since), default=0),
                orders=Count("id"),
            )
            .order_by("-total_cents")
        ),
        "weekly_signups": weekly_counts(User.objects.all(), field="date_joined"),
        "weekly_enrolments": weekly_counts(enrolments),
        "top_courses": [
            {
                "slug": c.slug,
                "title": c.title,
                "instructor": c.instructor.get_full_name() or c.instructor.username,
                "new_enrolments": c.recent,
                "enrolled": c.enrolled,
            }
            for c in top
        ],
    }
