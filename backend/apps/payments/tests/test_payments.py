import hashlib
import hmac
import json
import time
from types import SimpleNamespace

import pytest
import stripe
from rest_framework.test import APIClient

from apps.learning.models import Enrollment
from apps.learning.tests.test_learning import CourseFactory
from apps.notifications.models import Notification
from apps.payments.models import Order


@pytest.fixture
def course(db):
    return CourseFactory(price_cents=4900)


@pytest.fixture
def stripe_session(monkeypatch):
    calls = []

    def create(**params):
        calls.append(params)
        return SimpleNamespace(id=f"cs_test_{len(calls)}", url="https://checkout.stripe.test/pay")

    monkeypatch.setattr(stripe.checkout.Session, "create", create)
    return calls


def deliver(payload: dict, key="whsec_test"):
    body = json.dumps(payload)
    t = int(time.time())
    sig = hmac.new(key.encode(), f"{t}.{body}".encode(), hashlib.sha256).hexdigest()
    return APIClient().post(
        "/api/payments/webhook/",
        body,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=f"t={t},v1={sig}",
    )


def completed(session_id, amount=4900, currency="usd", status="paid", total=None):
    return {
        "id": "evt_1",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": session_id,
                "object": "checkout.session",
                "payment_status": status,
                "amount_subtotal": amount,
                "amount_total": amount if total is None else total,
                "currency": currency,
                "payment_intent": f"pi_{session_id}",
            }
        },
    }


@pytest.mark.django_db
def test_paid_course_needs_checkout(auth_client, course):
    r = auth_client.post(f"/api/courses/{course.slug}/enroll/")
    assert r.status_code == 402
    assert r.json()["detail"] == "Buy this course to enrol."
    assert not Enrollment.objects.exists()
    free = CourseFactory()
    assert auth_client.post(f"/api/courses/{free.slug}/enroll/").status_code == 201


@pytest.mark.django_db
def test_checkout_creates_an_order_and_a_hosted_page(user, auth_client, course, stripe_session):
    r = auth_client.post("/api/payments/checkout/", {"course": course.slug})
    assert r.status_code == 200
    assert r.json() == {"url": "https://checkout.stripe.test/pay"}
    order = Order.objects.get()
    assert (order.buyer, order.amount_cents, order.currency) == (user, 4900, "usd")
    assert order.checkout_session == "cs_test_1"
    sent = stripe_session[0]
    assert sent["client_reference_id"] == str(order.id)
    assert sent["line_items"][0]["price_data"]["unit_amount"] == 4900
    assert sent["success_url"].endswith(f"/courses/{course.slug}?paid=1")
    assert sent["allow_promotion_codes"] is True


@pytest.mark.django_db
def test_checkout_rules(user, auth_client, course, stripe_session, settings):
    free = CourseFactory()
    assert auth_client.post("/api/payments/checkout/", {"course": free.slug}).status_code == 400
    draft = CourseFactory(price_cents=900, status="draft")
    assert auth_client.post("/api/payments/checkout/", {"course": draft.slug}).status_code == 404
    Enrollment.objects.create(course=course, student=user)
    assert auth_client.post("/api/payments/checkout/", {"course": course.slug}).status_code == 400
    settings.STRIPE_SECRET_KEY = ""
    assert auth_client.post("/api/payments/checkout/", {"course": course.slug}).status_code == 503
    assert not stripe_session and not Order.objects.exists()


@pytest.mark.django_db
def test_provider_failure_leaves_no_order(auth_client, course, monkeypatch):
    def fail(**_):
        raise stripe.APIConnectionError("down")

    monkeypatch.setattr(stripe.checkout.Session, "create", fail)
    assert auth_client.post("/api/payments/checkout/", {"course": course.slug}).status_code == 502
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_signed_payment_enrols_once(
    user, auth_client, course, stripe_session, django_capture_on_commit_callbacks
):
    auth_client.post("/api/payments/checkout/", {"course": course.slug})
    with django_capture_on_commit_callbacks(execute=True):
        assert deliver(completed("cs_test_1")).status_code == 200
    assert deliver(completed("cs_test_1")).status_code == 200, "Stripe retries are harmless"
    order = Order.objects.get()
    assert order.status == "paid" and order.paid_at
    assert Enrollment.objects.filter(course=course, student=user).count() == 1
    assert Notification.objects.filter(recipient=course.instructor).count() == 1


@pytest.mark.django_db
def test_webhook_rejects_what_it_cannot_trust(user, auth_client, course, stripe_session):
    auth_client.post("/api/payments/checkout/", {"course": course.slug})
    assert deliver(completed("cs_test_1"), key="whsec_forged").status_code == 400
    assert (
        APIClient()
        .post("/api/payments/webhook/", completed("cs_test_1"), format="json")
        .status_code
        == 400
    )
    assert deliver(completed("cs_test_1", status="unpaid")).status_code == 200
    assert deliver(completed("cs_test_1", amount=1)).status_code == 200
    assert deliver(completed("cs_unknown")).status_code == 200
    assert Order.objects.get().status == "pending"
    assert not Enrollment.objects.exists()


@pytest.mark.django_db
def test_instructor_sets_a_price(course):
    c = APIClient()
    c.force_authenticate(course.instructor)
    url = f"/api/courses/{course.slug}/"
    assert c.patch(url, {"price_cents": 20}).status_code == 400
    r = c.patch(url, {"price_cents": 1500, "currency": "eur"})
    assert r.status_code == 200
    assert (r.json()["price_cents"], r.json()["currency"]) == (1500, "usd"), (
        "currency is the site's"
    )


def refunded(payment_intent, full=True):
    return {
        "id": "evt_2",
        "object": "event",
        "type": "charge.refunded",
        "data": {
            "object": {
                "id": "ch_1",
                "object": "charge",
                "payment_intent": payment_intent,
                "refunded": full,
            }
        },
    }


@pytest.mark.django_db
def test_a_promotion_code_lowers_what_was_paid(user, auth_client, course, stripe_session):
    auth_client.post("/api/payments/checkout/", {"course": course.slug})
    assert deliver(completed("cs_test_1", total=2450)).status_code == 200
    order = Order.objects.get()
    assert (order.status, order.amount_cents, order.paid_cents) == ("paid", 4900, 2450)
    assert order.payment_intent == "pi_cs_test_1"
    assert Enrollment.objects.filter(student=user).exists()


@pytest.mark.django_db
def test_a_full_refund_ends_access(user, auth_client, course, stripe_session):
    auth_client.post("/api/payments/checkout/", {"course": course.slug})
    deliver(completed("cs_test_1"))
    assert deliver(refunded("pi_cs_test_1", full=False)).status_code == 200
    assert Enrollment.objects.filter(student=user).exists(), "a partial refund keeps access"
    assert deliver(refunded("pi_cs_test_1")).status_code == 200
    assert deliver(refunded("pi_cs_test_1")).status_code == 200, "retries are harmless"
    assert Order.objects.get().status == "refunded"
    assert not Enrollment.objects.filter(student=user).exists()
    assert deliver(refunded("pi_unknown")).status_code == 200


@pytest.mark.django_db
def test_course_revenue_for_its_instructor(user, auth_client, course, stripe_session):
    url = f"/api/payments/courses/{course.slug}/revenue/"
    auth_client.post("/api/payments/checkout/", {"course": course.slug})
    deliver(completed("cs_test_1", total=3900))
    assert auth_client.get(url).status_code == 403
    c = APIClient()
    c.force_authenticate(course.instructor)
    assert c.get(url).json() == [
        {"currency": "usd", "total_cents": 3900, "recent_cents": 3900, "orders": 1}
    ]
    deliver(refunded("pi_cs_test_1"))
    assert c.get(url).json() == [], "refunds come off the total"


@pytest.mark.django_db
def test_no_second_purchase_and_a_duplicate_refund_keeps_access(
    user, auth_client, course, stripe_session
):
    auth_client.post("/api/payments/checkout/", {"course": course.slug})
    auth_client.post("/api/payments/checkout/", {"course": course.slug})  # a second tab
    deliver(completed("cs_test_1"))
    assert auth_client.post("/api/payments/checkout/", {"course": course.slug}).status_code == 400
    deliver(completed("cs_test_2"))  # the second tab paid too
    assert Order.objects.filter(status="paid").count() == 2
    deliver(refunded("pi_cs_test_2"))  # support refunds the duplicate
    assert Enrollment.objects.filter(student=user, course=course).exists()
