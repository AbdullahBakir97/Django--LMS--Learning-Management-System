import pytest
from rest_framework.test import APIClient

from conftest import UserFactory

PASSWORD = "an-old-long-password-1"  # noqa: S105
NEW = {"new_password1": "a-new-long-password-2", "new_password2": "a-new-long-password-2"}


@pytest.fixture
def signed_in(db):
    user = UserFactory()
    user.set_password(PASSWORD)
    user.save()
    from allauth.account.models import EmailAddress

    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    client = APIClient()
    r = client.post("/api/auth/login/", {"email": user.email, "password": PASSWORD})
    assert r.status_code == 200, r.data
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    return user, client


def test_changing_the_password_needs_the_old_one(signed_in):
    user, client = signed_in
    assert client.post("/api/auth/password/change/", NEW).status_code == 400
    r = client.post("/api/auth/password/change/", {**NEW, "old_password": PASSWORD})
    assert r.status_code == 200, r.data


def test_a_new_password_signs_out_every_device(signed_in):
    user, client = signed_in
    token = client.cookies["lms_refresh"].value
    client.post("/api/auth/password/change/", {**NEW, "old_password": PASSWORD})
    other_device = APIClient()
    other_device.cookies["lms_refresh"] = token
    assert other_device.post("/api/auth/token/refresh/").status_code == 401
