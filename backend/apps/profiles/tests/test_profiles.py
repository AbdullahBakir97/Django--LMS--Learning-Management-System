import pytest
from rest_framework.test import APIClient

from apps.profiles.models import Profile, Skill
from conftest import UserFactory


@pytest.mark.django_db
def test_profile_is_created_with_user(user):
    assert Profile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_me_returns_and_updates_own_profile(auth_client, user):
    response = auth_client.get("/api/profiles/me/")
    assert response.status_code == 200
    assert response.data["user"]["username"] == user.username

    response = auth_client.patch("/api/profiles/me/", {"headline": "Backend engineer"})
    assert response.status_code == 200
    assert response.data["headline"] == "Backend engineer"


@pytest.mark.django_db
def test_public_profile_by_username(auth_client):
    other = UserFactory(username="nour")
    response = auth_client.get("/api/profiles/nour/")
    assert response.status_code == 200
    assert response.data["user"]["id"] == other.id
    assert auth_client.get("/api/profiles/nobody/").status_code == 404


@pytest.mark.django_db
def test_anonymous_is_rejected(api_client):
    assert api_client.get("/api/profiles/me/").status_code == 401


@pytest.mark.django_db
def test_experience_crud_is_scoped_to_owner(auth_client, user):
    payload = {"title": "Engineer", "company": "ACME", "start_date": "2023-01-01"}
    response = auth_client.post("/api/profiles/me/experiences/", payload)
    assert response.status_code == 201, response.data
    experience_id = response.data["id"]

    other_client = APIClient()
    other_client.force_authenticate(UserFactory())
    assert other_client.get(f"/api/profiles/me/experiences/{experience_id}/").status_code == 404
    assert other_client.delete(f"/api/profiles/me/experiences/{experience_id}/").status_code == 404

    response = auth_client.patch(
        f"/api/profiles/me/experiences/{experience_id}/", {"end_date": "2022-12-31"}
    )
    assert response.status_code == 400
    assert "end_date" in response.data["errors"]

    assert auth_client.delete(f"/api/profiles/me/experiences/{experience_id}/").status_code == 204


@pytest.mark.django_db
def test_add_skill_reuses_taxonomy_and_rejects_duplicates(auth_client):
    Skill.objects.create(name="Python")
    response = auth_client.post("/api/profiles/me/skills/", {"name": "python", "level": "expert"})
    assert response.status_code == 201, response.data
    assert response.data == {
        "id": response.data["id"],
        "name": "Python",
        "level": "expert",
        "endorsement_count": 0,
    }
    assert Skill.objects.count() == 1

    response = auth_client.post("/api/profiles/me/skills/", {"name": "Python"})
    assert response.status_code == 400


@pytest.mark.django_db
def test_endorsements(auth_client, user):
    owner = UserFactory(username="sami")
    owner_client = APIClient()
    owner_client.force_authenticate(owner)
    skill_id = owner_client.post("/api/profiles/me/skills/", {"name": "Django"}).data["id"]
    url = f"/api/profiles/sami/skills/{skill_id}/endorse/"

    assert owner_client.post(url).status_code == 403, "no self-endorsement"
    assert auth_client.post(url).status_code == 201
    assert auth_client.post(url).status_code == 201, "endorsing twice is idempotent"
    assert auth_client.get("/api/profiles/sami/").data["skills"][0]["endorsement_count"] == 1
    assert auth_client.delete(url).status_code == 204
    assert auth_client.get("/api/profiles/sami/").data["skills"][0]["endorsement_count"] == 0


@pytest.mark.django_db
def test_skill_search(auth_client):
    Skill.objects.create(name="Python")
    Skill.objects.create(name="PostgreSQL")
    names = [s["name"] for s in auth_client.get("/api/skills/?search=py").data]
    assert names == ["Python"]
