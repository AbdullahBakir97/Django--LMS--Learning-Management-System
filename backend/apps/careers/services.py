"""Writes with rules. Every function takes the acting user first."""

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core import events
from apps.profiles.models import Skill

from . import events as names
from .models import (
    Application,
    Company,
    CompanyFollower,
    CompanyMember,
    CompanyUpdate,
    Interview,
    Job,
    SavedJob,
)
from .selectors import role_in

MAX_RESUME_BYTES = 5 * 1024 * 1024
Role = CompanyMember.Role
Status = Application.Status


def _name(user) -> str:
    return user.get_full_name() or user.username


def _require_team(actor, company, admin=False):
    role = role_in(actor, company)
    if role is None or (admin and role != Role.ADMIN):
        if actor.role != "admin":
            raise PermissionDenied(
                "Only the company's admins can do this."
                if admin
                else "Only the company's team can do this."
            )


@transaction.atomic
def create_company(actor, **fields) -> Company:
    company = Company.objects.create(**fields)
    CompanyMember.objects.create(company=company, user=actor, role=Role.ADMIN)
    return company


def update_company(actor, company: Company, **fields) -> Company:
    _require_team(actor, company, admin=True)
    for key, value in fields.items():
        setattr(company, key, value)
    company.save()
    return company


def add_member(actor, company: Company, user, role: str) -> CompanyMember:
    _require_team(actor, company, admin=True)
    admins = CompanyMember.objects.filter(company=company, role=Role.ADMIN)
    if role != Role.ADMIN and admins.filter(user=user).exists() and admins.count() == 1:
        raise ValidationError("A company needs at least one admin.")
    member, _ = CompanyMember.objects.update_or_create(
        company=company, user=user, defaults={"role": role}
    )
    return member


def remove_member(actor, company: Company, user_id) -> None:
    _require_team(actor, company, admin=True)
    admins = CompanyMember.objects.filter(company=company, role=Role.ADMIN)
    if admins.filter(user_id=user_id).exists() and admins.count() == 1:
        raise ValidationError("A company needs at least one admin.")
    CompanyMember.objects.filter(company=company, user_id=user_id).delete()


def follow(actor, company: Company) -> None:
    CompanyFollower.objects.get_or_create(company=company, user=actor)


def unfollow(actor, company: Company) -> None:
    CompanyFollower.objects.filter(company=company, user=actor).delete()


def _skills(names) -> list[Skill]:
    """Names as people type them; an unknown skill joins the shared taxonomy."""
    out = []
    for name in dict.fromkeys(n.strip() for n in names if n.strip()):
        skill = Skill.objects.filter(name__iexact=name).first() or Skill.objects.create(name=name)
        out.append(skill)
    return out


def create_job(actor, company: Company, skills=(), **fields) -> Job:
    _require_team(actor, company)
    job = Job.objects.create(company=company, posted_by=actor, **fields)
    job.skills.set(_skills(skills))
    return job


def update_job(actor, job: Job, skills=None, **fields) -> Job:
    _require_team(actor, job.company)
    for key, value in fields.items():
        setattr(job, key, value)
    job.save()
    if skills is not None:
        job.skills.set(_skills(skills))
    return job


def publish_job(actor, job: Job) -> Job:
    _require_team(actor, job.company)
    job.status = Job.Status.OPEN
    job.published_at = job.published_at or timezone.now()
    job.save(update_fields=["status", "published_at", "updated_at"])
    return job


def close_job(actor, job: Job) -> Job:
    _require_team(actor, job.company)
    job.status = Job.Status.CLOSED
    job.save(update_fields=["status", "updated_at"])
    return job


def delete_job(actor, job: Job) -> None:
    _require_team(actor, job.company)
    if job.applications.exists():
        raise ValidationError("A job with applications can be closed, not deleted.")
    job.delete()


def save_job(actor, job: Job) -> None:
    SavedJob.objects.get_or_create(job=job, user=actor)


def unsave_job(actor, job: Job) -> None:
    SavedJob.objects.filter(job=job, user=actor).delete()


def _check_resume(upload) -> None:
    if upload.size > MAX_RESUME_BYTES:
        raise ValidationError({"resume": "Keep the résumé under 5 MB."})
    head = upload.read(5)
    upload.seek(0)
    if head != b"%PDF-":
        raise ValidationError({"resume": "Upload a PDF."})


def apply(actor, job: Job, resume, cover_letter: str = "") -> Application:
    if job.status != Job.Status.OPEN:
        raise ValidationError("This job is not taking applications.")
    if role_in(actor, job.company) is not None:
        raise ValidationError("You work at this company.")
    _check_resume(resume)
    try:
        with transaction.atomic():
            application = Application.objects.create(
                job=job, applicant=actor, resume=resume, cover_letter=cover_letter
            )
    except IntegrityError:
        raise ValidationError("You have already applied to this job.") from None
    events.publish(
        names.APPLICATION_SUBMITTED,
        application_id=application.id,
        job_id=job.id,
        job_title=job.title,
        applicant_id=actor.id,
        applicant_name=_name(actor),
        team_ids=list(job.company.members.values_list("user_id", flat=True)),
    )
    return application


def withdraw(actor, application: Application) -> Application:
    if application.applicant_id != actor.id:
        raise PermissionDenied("Only the applicant can withdraw.")
    if application.status in (Status.HIRED, Status.WITHDRAWN):
        raise ValidationError("This application can no longer be withdrawn.")
    return _set(application, Status.WITHDRAWN)


def set_status(actor, application: Application, status: str) -> Application:
    _require_team(actor, application.job.company)
    if status == Status.WITHDRAWN or application.status == Status.WITHDRAWN:
        raise ValidationError("Only the applicant withdraws, and a withdrawn application stays so.")
    if status == application.status:
        return application
    _set(application, status)
    events.publish(
        names.APPLICATION_STATUS_CHANGED,
        application_id=application.id,
        applicant_id=application.applicant_id,
        job_id=application.job_id,
        job_title=application.job.title,
        company_name=application.job.company.name,
        status=status,
        status_label=Status(status).label,
    )
    return application


def _set(application: Application, status: str) -> Application:
    application.status = status
    application.status_changed_at = timezone.now()
    application.save(update_fields=["status", "status_changed_at", "updated_at"])
    return application


CLOSED = (Status.REJECTED, Status.WITHDRAWN, Status.HIRED)
SLOT_FIELDS = ("starts_at", "duration_minutes", "kind", "location")


def _interview_payload(interview: Interview) -> dict:
    job = interview.application.job
    return {
        "interview_id": interview.id,
        "applicant_id": interview.application.applicant_id,
        "applicant_name": _name(interview.application.applicant),
        "job_id": job.id,
        "job_title": job.title,
        "company_name": job.company.name,
        "starts_at": interview.starts_at.isoformat(),
        "team_ids": list(job.company.members.values_list("user_id", flat=True)),
    }


def schedule_interview(actor, application: Application, **fields) -> Interview:
    _require_team(actor, application.job.company)
    if application.status in CLOSED:
        raise ValidationError("This application is closed.")
    interview = Interview.objects.create(application=application, scheduled_by=actor, **fields)
    if application.status in (Status.SUBMITTED, Status.REVIEWING):
        _set(application, Status.INTERVIEW)  # the interview notification says it all
    events.publish(names.INTERVIEW_SCHEDULED, rescheduled=False, **_interview_payload(interview))
    return interview


def update_interview(actor, interview: Interview, **fields) -> Interview:
    """Team edits. A new time, length, kind or place needs the candidate's reply again."""
    _require_team(actor, interview.application.job.company)
    if interview.status == Interview.Status.CANCELLED:
        raise ValidationError("This interview was cancelled.")
    moved = any(k in fields and fields[k] != getattr(interview, k) for k in SLOT_FIELDS)
    for key, value in fields.items():
        setattr(interview, key, value)
    if moved:
        interview.status, interview.response_note = Interview.Status.SCHEDULED, ""
    interview.save()
    if moved:
        events.publish(names.INTERVIEW_SCHEDULED, rescheduled=True, **_interview_payload(interview))
    return interview


def respond_to_interview(actor, interview: Interview, accept: bool, note: str = "") -> Interview:
    if interview.application.applicant_id != actor.id:
        raise PermissionDenied("Only the candidate replies.")
    if interview.status == Interview.Status.CANCELLED or interview.starts_at <= timezone.now():
        raise ValidationError("This interview can no longer be answered.")
    interview.status = Interview.Status.CONFIRMED if accept else Interview.Status.DECLINED
    interview.response_note = note
    interview.save(update_fields=["status", "response_note", "updated_at"])
    events.publish(
        names.INTERVIEW_RESPONDED,
        accepted=accept,
        **_interview_payload(interview),
    )
    return interview


def cancel_interview(actor, interview: Interview) -> Interview:
    _require_team(actor, interview.application.job.company)
    if interview.status != Interview.Status.CANCELLED:
        interview.status = Interview.Status.CANCELLED
        interview.save(update_fields=["status", "updated_at"])
        events.publish(names.INTERVIEW_CANCELLED, **_interview_payload(interview))
    return interview


def post_update(actor, company: Company, body: str) -> CompanyUpdate:
    _require_team(actor, company)
    return CompanyUpdate.objects.create(company=company, author=actor, body=body)


def delete_update(actor, update: CompanyUpdate) -> None:
    _require_team(actor, update.company)
    update.delete()
