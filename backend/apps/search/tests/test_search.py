from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.careers.models import Company, CompanyMember, Job
from apps.community.models import Event, Group
from apps.learning.models import Course
from conftest import UserFactory


@pytest.fixture
def world(user):
    teacher = UserFactory(first_name="Karim", last_name="Nassar", username="karim")
    teacher.profile.headline = "Teaches Django and APIs"
    teacher.profile.save()
    Course.objects.create(instructor=teacher, title="Django REST APIs", status="published")
    Course.objects.create(instructor=teacher, title="Django secrets (draft)")
    public = Group.objects.create(owner=teacher, name="Django Amman", slug="django-amman")
    hidden = Group.objects.create(
        owner=teacher, name="Core team", slug="core-team", privacy=Group.Privacy.PRIVATE
    )
    soon = timezone.now() + timedelta(days=3)
    for title, group in [("Django meetup", public), ("Django planning", hidden)]:
        Event.objects.create(
            host=teacher,
            group=group,
            title=title,
            starts_at=soon,
            ends_at=soon + timedelta(hours=2),
        )
    nahla = Company.objects.create(name="Nahla Labs", slug="nahla", industry="Software")
    CompanyMember.objects.create(company=nahla, user=teacher, role="admin")
    Job.objects.create(company=nahla, title="Django developer", description="APIs", status="open")
    Job.objects.create(company=nahla, title="Django lead", description="Draft", status="draft")
    return teacher


def titles(response, kind):
    return [hit["title"] for hit in response.data[kind]]


@pytest.mark.django_db
def test_one_search_across_kinds_respects_visibility(world, auth_client):
    r = auth_client.get("/api/search/", {"q": "djan"})  # a prefix, as while typing
    assert r.status_code == 200
    assert titles(r, "people") == ["Karim Nassar"]
    assert titles(r, "courses") == ["Django REST APIs"], "drafts stay with their instructor"
    assert titles(r, "groups") == ["Django Amman"]
    assert titles(r, "events") == ["Django meetup"], "private group events stay private"
    assert titles(r, "jobs") == ["Django developer"], "drafts stay with the hiring team"
    assert r.data["courses"][0]["url"] == "/courses/django-rest-apis"
    assert r.data["people"][0]["subtitle"] == "Teaches Django and APIs"

    mine = auth_client.get("/api/search/", {"q": "django"})
    assert titles(mine, "companies") == []
    assert titles(auth_client.get("/api/search/", {"q": "nahla software"}), "companies") == [
        "Nahla Labs"
    ]


@pytest.mark.django_db
def test_insiders_see_their_own_drafts(world):
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(world)
    r = client.get("/api/search/", {"q": "django", "type": "courses"})
    assert set(titles(r, "courses")) == {"Django REST APIs", "Django secrets (draft)"}
    assert list(r.data) == ["courses"]


@pytest.mark.django_db
def test_title_matches_rank_above_description_matches(world, auth_client):
    Course.objects.create(
        instructor=world, title="Python basics", description="Leads into APIs", status="published"
    )
    r = auth_client.get("/api/search/", {"q": "apis", "type": "courses"})
    assert titles(r, "courses") == ["Django REST APIs", "Python basics"]


@pytest.mark.django_db
def test_odd_input(auth_client, api_client):
    assert all(v == [] for v in auth_client.get("/api/search/", {"q": "  !!  "}).data.values())
    assert auth_client.get("/api/search/", {"q": "x", "type": "nope"}).status_code == 400
    assert auth_client.get("/api/search/", {"q": "a:* | b & !c ('"}).status_code == 200
    assert api_client.get("/api/search/", {"q": "x"}).status_code == 401


@pytest.mark.django_db
def test_query_count_stays_flat_as_results_grow(world, auth_client):
    def count():
        with CaptureQueriesContext(connection) as ctx:
            auth_client.get("/api/search/", {"q": "django"})
        return len(ctx.captured_queries)

    before = count()
    nahla = Company.objects.get(slug="nahla")
    for i in range(4):
        Course.objects.create(instructor=world, title=f"Django {i}", status="published")
        Job.objects.create(company=nahla, title=f"Django {i}", description="x", status="open")
        UserFactory(first_name="Django", last_name=f"Fan{i}")
    assert count() == before <= 8  # one query per kind, plus job skills
