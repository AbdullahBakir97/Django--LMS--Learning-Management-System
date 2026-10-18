"""Stripe Checkout for paid courses. Stripe hosts the card form, so card data never reaches us."""

import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from apps.learning import services as learning
from apps.learning.models import Course

from .models import Order

log = logging.getLogger(__name__)


class PaymentsUnavailable(APIException):
    status_code = 503
    default_detail = "Payments are not set up on this site."


class ProviderError(APIException):
    status_code = 502
    default_detail = "Could not reach the payment provider. Try again in a moment."


@transaction.atomic
def start_checkout(actor, course: Course) -> str:
    """Create a pending order and a hosted checkout page for it. Returns the page's URL."""
    if not settings.STRIPE_SECRET_KEY:
        raise PaymentsUnavailable()
    learning.check_can_enroll(actor, course)
    if not course.is_paid:
        raise ValidationError("This course is free. Enrol directly.")
    order = Order.objects.create(
        buyer=actor, course=course, amount_cents=course.price_cents, currency=course.currency
    )
    page = f"{settings.FRONTEND_URL}/courses/{course.slug}"
    try:
        session = stripe.checkout.Session.create(
            api_key=settings.STRIPE_SECRET_KEY,
            idempotency_key=f"order-{order.id}",
            mode="payment",
            client_reference_id=str(order.id),
            customer_email=actor.email or None,
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": order.currency,
                        "unit_amount": order.amount_cents,
                        "product_data": {"name": course.title},
                    },
                }
            ],
            success_url=f"{page}?paid=1",
            cancel_url=page,
        )
    except stripe.StripeError as exc:
        raise ProviderError() from exc
    order.checkout_session = session.id
    order.save(update_fields=["checkout_session", "updated_at"])
    return session.url


def parse_event(payload: bytes, signature: str | None):
    """The webhook's trust boundary: anything Stripe did not sign is rejected."""
    try:
        return stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise ValidationError("Invalid webhook signature.") from exc


PAID_EVENTS = {"checkout.session.completed", "checkout.session.async_payment_succeeded"}


@transaction.atomic
def handle_event(event) -> None:
    if event["type"] not in PAID_EVENTS:
        return
    session = event["data"]["object"]
    if session["payment_status"] != "paid":
        return  # bank transfers etc. finish later with async_payment_succeeded
    order = (
        Order.objects.select_for_update()
        .select_related("buyer", "course")
        .filter(checkout_session=session["id"])
        .first()
    )
    if order is None or order.status == Order.Status.PAID:
        return  # not ours, or Stripe retried a delivery we already handled
    if session["amount_total"] != order.amount_cents or session["currency"] != order.currency:
        # Answering an error would make Stripe retry forever; leave it pending for staff.
        log.error(
            "Order %s paid %s %s, expected %s %s",
            order.id,
            session["amount_total"],
            session["currency"],
            order.amount_cents,
            order.currency,
        )
        return
    order.status = Order.Status.PAID
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "paid_at", "updated_at"])
    learning.enroll(order.buyer, order.course, paid=True)
