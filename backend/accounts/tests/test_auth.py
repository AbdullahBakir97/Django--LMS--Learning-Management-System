import re

import pytest
from django.core import mail

from accounts.models import User

REGISTER = {
    "username": "amina",
    "email": "amina@example.com",
    "password1": "a-strong-password-42",
    "password2": "a-strong-password-42",
}


def _key_from_last_email():
    body = mail.outbox[-1].body
    return re.search(r"confirm-email/([^/\s]+)/", body).group(1)


@pytest.mark.django_db
def test_register_verify_login_refresh_logout(api_client):
    response = api_client.post("/api/auth/register/", REGISTER)
    assert response.status_code == 201, response.data
    assert len(mail.outbox) == 1

    # Unverified users cannot log in.
    response = api_client.post(
        "/api/auth/login/", {"email": REGISTER["email"], "password": REGISTER["password1"]}
    )
    assert response.status_code == 400

    response = api_client.post("/api/auth/verify-email/", {"key": _key_from_last_email()})
    assert response.status_code == 200

    response = api_client.post(
        "/api/auth/login/", {"email": REGISTER["email"], "password": REGISTER["password1"]}
    )
    assert response.status_code == 200, response.data
    assert "access" in response.data
    assert not response.data.get("refresh"), "refresh token must only travel in the cookie"
    refresh_cookie = response.cookies["lms_refresh"]
    assert refresh_cookie["httponly"]
    assert refresh_cookie["path"] == "/api/auth/token/refresh/"
    assert response.data["user"]["role"] == "learner"

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    response = api_client.get("/api/auth/user/")
    assert response.status_code == 200
    assert response.data["username"] == "amina"

    api_client.credentials()
    response = api_client.post("/api/auth/token/refresh/")
    assert response.status_code == 200
    assert "access" in response.data

    response = api_client.post("/api/auth/logout/")
    assert response.status_code == 200
    assert api_client.cookies["lms_refresh"].value == ""


@pytest.mark.django_db
def test_register_rejects_duplicate_email(api_client, user):
    response = api_client.post("/api/auth/register/", {**REGISTER, "email": user.email})
    assert response.status_code == 400
    assert "email" in response.data["errors"]


@pytest.mark.django_db
def test_password_reset_email_links_to_frontend(api_client, user, settings):
    settings.FRONTEND_URL = "https://app.example.com"
    response = api_client.post("/api/auth/password/reset/", {"email": user.email})
    assert response.status_code == 200
    link = re.search(r"https?://\S+reset-password/\S+", mail.outbox[-1].body).group(0)
    response = api_client.get(link.split("testserver")[-1])
    assert response.status_code == 302
    assert response["Location"].startswith("https://app.example.com/reset-password/")


@pytest.mark.django_db
def test_user_cannot_change_own_role(auth_client, user):
    response = auth_client.patch("/api/auth/user/", {"role": "admin", "first_name": "Ada"})
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.role == User.Role.LEARNER
    assert user.first_name == "Ada"
