from datetime import timedelta

import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.test import APIClient

from apps.careers.ics import interview_ics
from apps.careers.models import Application, Interview, Job
from apps.notifications.models import Notification
from apps.profiles.models import ProfileSkill, Skill
from conftest import UserFactory

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def pdf(content=PDF, name="cv.pdf"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


@pytest.fixture
def run_events(django_capture_on_commit_callbacks):
    return lambda: django_capture_on_commit_callbacks(execute=True)


@pytest.fixture
def recruiter(db):
    return UserFactory(first_name="Rana", last_name="Odeh")


@pytest.fixture
def company(recruiter):
    return (
        client_for(recruiter).post("/api/companies/", {"name": "Nahla Labs", "size": "11-50"}).data
    )


def post_job(recruiter, company, **extra):
    data = {
        "company_slug": company["slug"],
        "title": "Backend engineer",
        "description": "Django and SQL.",
        "workplace": "hybrid",
        "level": "mid",
        "salary_min": 1200,
        "salary_max": 1800,
        "currency": "JOD",
        **extra,
    }
    return client_for(recruiter).post("/api/jobs/", data, format="json")


@pytest.mark.django_db
def test_company_team_and_drafts(recruiter, company, auth_client, user):
    assert company["slug"] == "nahla-labs" and company["my_role"] == "admin"
    assert post_job(user, company).status_code == 403, "outsiders cannot post jobs"
    job = post_job(recruiter, company).data
    assert job["status"] == "draft"
    assert auth_client.get(f"/api/jobs/{job['id']}/").status_code == 404, "drafts are private"
    assert auth_client.get("/api/jobs/").data["results"] == []

    rc = client_for(recruiter)
    assert rc.post(f"/api/jobs/{job['id']}/publish/").data["status"] == "open"
    listed = auth_client.get("/api/jobs/").data["results"]
    assert [j["title"] for j in listed] == ["Backend engineer"]
    assert listed[0]["applicant_count"] is None, "only the team sees applicant counts"

    assert (
        auth_client.post(
            f"/api/companies/{company['slug']}/members/",
            {"username": user.username, "role": "recruiter"},
        ).status_code
        == 403
    )
    assert (
        rc.post(
            f"/api/companies/{company['slug']}/members/",
            {"username": user.username, "role": "recruiter"},
        ).status_code
        == 201
    )
    assert (
        rc.delete(f"/api/companies/{company['slug']}/members/{recruiter.id}/").status_code == 400
    ), "last admin stays"
    assert auth_client.get(f"/api/companies/{company['slug']}/members/").status_code == 200


@pytest.mark.django_db
def test_salary_band_rules(recruiter, company):
    assert post_job(recruiter, company, salary_min=2000, salary_max=1000).status_code == 400
    assert post_job(recruiter, company, currency="").status_code == 400
    job = Job.objects.create(company_id=company["id"], title="x", description="y")
    job.salary_min, job.salary_max = 10, 5
    with pytest.raises(IntegrityError):
        job.save()


@pytest.mark.django_db
def test_apply_review_and_resume_privacy(recruiter, company, auth_client, user, run_events):
    rc = client_for(recruiter)
    jid = post_job(recruiter, company).data["id"]
    draft = auth_client.post(f"/api/jobs/{jid}/apply/", {"resume": pdf()})
    assert draft.status_code == 404, "drafts are invisible to applicants"
    rc.post(f"/api/jobs/{jid}/publish/")

    assert (
        auth_client.post(f"/api/jobs/{jid}/apply/", {"resume": pdf(b"MZ not a pdf")}).status_code
        == 400
    )
    with run_events():
        applied = auth_client.post(
            f"/api/jobs/{jid}/apply/", {"resume": pdf(), "cover_letter": "Hello"}
        )
    assert applied.status_code == 201
    assert auth_client.post(f"/api/jobs/{jid}/apply/", {"resume": pdf()}).status_code == 400, "once"
    assert rc.post(f"/api/jobs/{jid}/apply/", {"resume": pdf()}).status_code == 400, "own company"
    assert Notification.objects.filter(recipient=recruiter, kind="application_received").exists()

    app_id = applied.data["id"]
    assert applied.data["resume_url"] == f"/api/applications/{app_id}/resume/"
    stranger = client_for(UserFactory())
    assert stranger.get(f"/api/applications/{app_id}/").status_code == 404
    assert stranger.get(f"/api/applications/{app_id}/resume/").status_code == 404
    assert stranger.get(f"/api/jobs/{jid}/applications/").status_code == 403
    resume = rc.get(f"/api/applications/{app_id}/resume/")
    assert resume.status_code == 200 and b"".join(resume.streaming_content).startswith(b"%PDF-")

    assert [a["id"] for a in rc.get(f"/api/jobs/{jid}/applications/").data["results"]] == [app_id]
    assert rc.get(f"/api/jobs/{jid}/").data["applicant_count"] == 1
    assert (
        auth_client.post(f"/api/applications/{app_id}/status/", {"status": "offer"}).status_code
        == 403
    )
    with run_events():
        moved = rc.post(f"/api/applications/{app_id}/status/", {"status": "interview"}).data
    assert moved["status"] == "interview"
    n = Notification.objects.get(recipient=user, kind="application_update")
    assert n.title == "Nahla Labs: your application for Backend engineer is now “Interviewing”"

    mine = auth_client.get("/api/applications/").data["results"]
    assert [(a["job"]["title"], a["status"]) for a in mine] == [("Backend engineer", "interview")]
    assert auth_client.get(f"/api/jobs/{jid}/").data["my_application"] == "interview"
    assert auth_client.post(f"/api/applications/{app_id}/withdraw/").data["status"] == "withdrawn"
    assert rc.post(f"/api/applications/{app_id}/status/", {"status": "offer"}).status_code == 400
    assert rc.delete(f"/api/jobs/{jid}/").status_code == 400, "close, do not delete"
    assert rc.post(f"/api/jobs/{jid}/close/").data["status"] == "closed"
    assert auth_client.get("/api/jobs/").data["results"] == []


@pytest.mark.django_db
def test_resume_size_limit(recruiter, company, auth_client):
    jid = post_job(recruiter, company).data["id"]
    client_for(recruiter).post(f"/api/jobs/{jid}/publish/")
    big = pdf(PDF + b"0" * (5 * 1024 * 1024))
    assert auth_client.post(f"/api/jobs/{jid}/apply/", {"resume": big}).status_code == 400
    assert not Application.objects.exists()


@pytest.mark.django_db
def test_saved_jobs_filters_and_skill_match(recruiter, company, auth_client, user):
    rc = client_for(recruiter)
    django, sql, go = (Skill.objects.create(name=n) for n in ("Django", "SQL", "Go"))
    ProfileSkill.objects.create(profile=user.profile, skill=django)
    ProfileSkill.objects.create(profile=user.profile, skill=sql)
    a = post_job(
        recruiter,
        company,
        title="Go engineer",
        skills=["Go"],
        workplace="remote",
        description="Go services.",
    ).data["id"]
    b = post_job(recruiter, company, title="Django engineer", skills=["Django", "SQL"]).data["id"]
    for jid in (a, b):
        rc.post(f"/api/jobs/{jid}/publish/")

    renamed = client_for(recruiter).patch(
        f"/api/jobs/{a}/", {"skills": ["go", "Kubernetes"]}, format="json"
    )
    assert renamed.data["skills"] == ["Go", "Kubernetes"], "known names reuse the taxonomy"
    client_for(recruiter).patch(f"/api/jobs/{a}/", {"skills": ["Go"]}, format="json")
    ranked = auth_client.get("/api/jobs/?sort=match").data["results"]
    assert [(j["title"], j["matching_skills"], j["skill_count"]) for j in ranked] == [
        ("Django engineer", 2, 2),
        ("Go engineer", 0, 1),
    ]
    assert [j["title"] for j in auth_client.get("/api/jobs/?workplace=remote").data["results"]] == [
        "Go engineer"
    ]
    assert [j["title"] for j in auth_client.get("/api/jobs/?search=django").data["results"]] == [
        "Django engineer"
    ]

    assert auth_client.post(f"/api/jobs/{a}/save/").data["saved"] is True
    assert [j["id"] for j in auth_client.get("/api/jobs/?saved=true").data["results"]] == [a]
    assert auth_client.delete(f"/api/jobs/{a}/save/").data["saved"] is False

    c = auth_client.post(f"/api/companies/{company['slug']}/follow/").data
    assert c["following"] and c["follower_count"] == 1 and c["open_jobs"] == 2


@pytest.fixture
def application(recruiter, company, user, auth_client):
    job = post_job(recruiter, company).data
    client_for(recruiter).post(f"/api/jobs/{job['id']}/publish/")
    response = auth_client.post(f"/api/jobs/{job['id']}/apply/", {"resume": pdf()})
    assert response.status_code == 201, response.data
    return response.data


def slot(**extra):
    return {
        "starts_at": (timezone.now() + timedelta(days=3)).isoformat(),
        "duration_minutes": 45,
        "kind": "video",
        "location": "https://meet.example.org/abc",
        **extra,
    }


@pytest.mark.django_db
def test_team_schedules_and_candidate_replies(
    recruiter,
    application,
    user,
    auth_client,
    run_events,
    settings,
):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    team = client_for(recruiter)
    url = f"/api/applications/{application['id']}/interviews/"

    assert auth_client.post(url, slot()).status_code == 403, "the candidate cannot schedule"
    past = slot(starts_at=(timezone.now() - timedelta(hours=1)).isoformat())
    assert team.post(url, past).status_code == 400
    assert team.post(url, slot(duration_minutes=5)).status_code == 400

    with run_events():
        created = team.post(url, slot())
    assert created.status_code == 201, created.data
    assert created.data["status"] == "scheduled"
    assert Application.objects.get(pk=application["id"]).status == "interview"
    invite = Notification.objects.get(recipient=user, kind="interview")
    assert "invited you" in invite.title
    assert any("invited you" in m.subject for m in mail.outbox)

    mine = auth_client.get("/api/applications/").data["results"][0]
    assert [i["id"] for i in mine["interviews"]] == [created.data["id"]]

    iid = created.data["id"]
    assert team.post(f"/api/interviews/{iid}/reply/", {"accept": True}).status_code == 403
    with run_events():
        reply = auth_client.post(
            f"/api/interviews/{iid}/reply/", {"accept": True, "note": "See you"}
        )
    assert reply.data["status"] == "confirmed"
    assert Notification.objects.filter(recipient=recruiter, kind="interview_reply").exists()

    # Changing the time needs a new reply; changing only the notes does not.
    team.patch(f"/api/interviews/{iid}/", {"details": "Bring a laptop"})
    assert Interview.objects.get(pk=iid).status == "confirmed"
    with run_events():
        moved = team.patch(f"/api/interviews/{iid}/", {"duration_minutes": 60})
    assert moved.data["status"] == "scheduled" and moved.data["response_note"] == ""
    assert Notification.objects.filter(recipient=user, title__contains="moved").exists()
    assert auth_client.patch(f"/api/interviews/{iid}/", {"duration_minutes": 30}).status_code == 403

    with run_events():
        assert team.post(f"/api/interviews/{iid}/cancel/").data["status"] == "cancelled"
    assert auth_client.post(f"/api/interviews/{iid}/reply/", {"accept": True}).status_code == 400

    stranger = client_for(UserFactory())
    assert stranger.get(f"/api/interviews/{iid}/calendar.ics/").status_code == 404
    ics = auth_client.get(f"/api/interviews/{iid}/calendar.ics/")
    assert ics["Content-Type"] == "text/calendar" and b"STATUS:CANCELLED" in ics.content


@pytest.mark.django_db
def test_closed_applications_take_no_interviews(recruiter, application, auth_client):
    auth_client.post(f"/api/applications/{application['id']}/withdraw/")
    url = f"/api/applications/{application['id']}/interviews/"
    assert client_for(recruiter).post(url, slot()).status_code == 400


@pytest.mark.django_db
def test_calendar_escapes_text_and_folds_long_lines(recruiter, application):
    interview = Interview.objects.create(
        application_id=application["id"],
        starts_at=timezone.now() + timedelta(days=1),
        location="Room 4, Building B; second floor",
        details="Line one\nLine two " + "x" * 120,
    )
    text = interview_ics(interview)
    assert "LOCATION:Room 4\\, Building B\\; second floor" in text
    assert "DESCRIPTION:Line one\\nLine two" in text
    assert all(len(line) <= 75 for line in text.split("\r\n"))
    assert text.endswith("END:VCALENDAR\r\n")
