import pytest
from rest_framework.exceptions import NotFound, ValidationError

from core import events
from core.exceptions import problem_details_exception_handler
from core.realtime import user_group


@pytest.mark.django_db
def test_health_reports_ok(client):
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": True, "cache": True}


@pytest.mark.django_db
def test_openapi_schema_is_served(client):
    response = client.get("/api/schema/")
    assert response.status_code == 200
    assert b"LMS API" in response.content


def test_problem_details_for_single_detail():
    response = problem_details_exception_handler(NotFound(), {})
    assert response["Content-Type"] == "application/problem+json"
    assert response.data == {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "detail": "Not found.",
    }


def test_problem_details_keeps_validation_errors():
    response = problem_details_exception_handler(ValidationError({"email": ["Required."]}), {})
    assert response.data["status"] == 400
    assert response.data["errors"] == {"email": ["Required."]}


@pytest.mark.django_db(transaction=True)
def test_events_are_delivered_after_commit():
    received = []
    events.subscribe("test.ping")(lambda **payload: received.append(payload))
    events.publish("test.ping", value=1)
    assert received == [{"value": 1}]


def test_user_group_name():
    assert user_group(7) == "user.7"
