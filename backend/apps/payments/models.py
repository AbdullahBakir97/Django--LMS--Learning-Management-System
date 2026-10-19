from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Order(TimeStampedModel):
    """One checkout for one course. Price and currency are copied, so later edits change nothing."""

    class Status(models.TextChoices):
        PENDING = "pending", "Waiting for payment"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    # PROTECT: an order is a financial record, it outlives neither side silently.
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    course = models.ForeignKey("learning.Course", on_delete=models.PROTECT, related_name="orders")
    amount_cents = models.PositiveIntegerField(help_text="The list price at checkout.")
    # What the buyer paid after any promotion code; set when paid.
    paid_cents = models.PositiveIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    checkout_session = models.CharField(max_length=255, unique=True, null=True, blank=True)
    payment_intent = models.CharField(max_length=255, unique=True, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["course", "status"], name="order_course_status_idx")]

    def __str__(self):
        return f"#{self.pk} {self.buyer} · {self.course} · {self.status}"
