import pytest

from conftest import UserFactory


@pytest.mark.django_db
def test_profiles_hide_email_and_deactivated_people(auth_client):
    other = UserFactory()
    data = auth_client.get(f"/api/profiles/{other.username}/").json()
    assert "email" not in data["user"]
    assert "email" in auth_client.get("/api/profiles/me/").json()["user"], "your own keeps it"
    other.is_active = False
    other.save()
    assert auth_client.get(f"/api/profiles/{other.username}/").status_code == 404
