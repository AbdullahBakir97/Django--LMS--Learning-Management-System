from django.db.models import Count, Exists, OuterRef, Q

from apps.profiles.models import ProfileSkill

from .models import Application, Company, CompanyFollower, CompanyMember, Job, SavedJob


def role_in(user, company) -> str | None:
    return (
        CompanyMember.objects.filter(company=company, user=user)
        .values_list("role", flat=True)
        .first()
    )


def companies(user):
    mine = CompanyMember.objects.filter(company=OuterRef("pk"), user=user)
    return Company.objects.annotate(
        open_jobs=Count("jobs", filter=Q(jobs__status=Job.Status.OPEN), distinct=True),
        follower_count=Count("followers", distinct=True),
        my_role=mine.values("role")[:1],
        following=Exists(CompanyFollower.objects.filter(company=OuterRef("pk"), user=user)),
    )


def jobs(user):
    """Open jobs for everyone; drafts and closed jobs also for the company's own team."""
    my_skills = ProfileSkill.objects.filter(profile__user=user).values("skill_id")
    team = CompanyMember.objects.filter(user=user).values("company_id")
    mine = Application.objects.filter(job=OuterRef("pk"), applicant=user)
    return (
        Job.objects.filter(Q(status=Job.Status.OPEN) | Q(company_id__in=team))
        .select_related("company")
        .prefetch_related("skills")
        .annotate(
            matching_skills=Count("skills", filter=Q(skills__in=my_skills), distinct=True),
            skill_count=Count("skills", distinct=True),
            saved=Exists(SavedJob.objects.filter(job=OuterRef("pk"), user=user)),
            my_application=mine.values("status")[:1],
            my_application_id=mine.values("id")[:1],
            applicant_count=Count("applications", distinct=True),
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
