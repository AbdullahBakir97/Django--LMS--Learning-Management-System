from django.db.models import Exists, OuterRef, Q

from apps.core.stats import count_of
from apps.profiles.models import ProfileSkill

from .models import (
    Application,
    Company,
    CompanyFollower,
    CompanyMember,
    CompanyUpdate,
    Job,
    SavedJob,
)


def role_in(user, company) -> str | None:
    return (
        CompanyMember.objects.filter(company=company, user=user)
        .values_list("role", flat=True)
        .first()
    )


def companies(user):
    mine = CompanyMember.objects.filter(company=OuterRef("pk"), user=user)
    return Company.objects.annotate(
        open_jobs=count_of(Job.objects.filter(company=OuterRef("pk"), status=Job.Status.OPEN)),
        follower_count=count_of(CompanyFollower.objects.filter(company=OuterRef("pk"))),
        my_role=mine.values("role")[:1],
        following=Exists(CompanyFollower.objects.filter(company=OuterRef("pk"), user=user)),
    )


def jobs(user):
    """Open jobs for everyone; drafts and closed jobs also for the company's own team."""
    my_skills = ProfileSkill.objects.filter(profile__user=user).values("skill_id")
    team = CompanyMember.objects.filter(user=user).values("company_id")
    mine = Application.objects.filter(job=OuterRef("pk"), applicant=user)
    job_skills = Job.skills.through.objects.filter(job=OuterRef("pk"))
    return (
        Job.objects.filter(Q(status=Job.Status.OPEN) | Q(company_id__in=team))
        .select_related("company")
        .prefetch_related("skills")
        .annotate(
            matching_skills=count_of(job_skills.filter(skill_id__in=my_skills)),
            skill_count=count_of(job_skills),
            saved=Exists(SavedJob.objects.filter(job=OuterRef("pk"), user=user)),
            my_application=mine.values("status")[:1],
            my_application_id=mine.values("id")[:1],
            applicant_count=count_of(Application.objects.filter(job=OuterRef("pk"))),
            on_team=Exists(CompanyMember.objects.filter(company=OuterRef("company"), user=user)),
        )
    )


def applications(user):
    """Yours, plus those to jobs at companies you work for."""
    team = CompanyMember.objects.filter(user=user).values("company_id")
    return (
        Application.objects.filter(Q(applicant=user) | Q(job__company_id__in=team))
        .select_related("job__company", "applicant__profile")
        .prefetch_related("interviews")
    )


def updates():
    return CompanyUpdate.objects.select_related("company", "author__profile")


def updates_for_follower(user):
    """News from the companies you follow, newest first."""
    followed = CompanyFollower.objects.filter(user=user).values("company_id")
    return updates().filter(company_id__in=followed)


def team_update_ids(user, rows) -> set[int]:
    team = set(CompanyMember.objects.filter(user=user).values_list("company_id", flat=True))
    return {u.id for u in rows if u.company_id in team or user.role == "admin"}
