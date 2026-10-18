import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


def unique_slug(model, value: str, max_length: int = 120) -> str:
    base = slugify(value)[:max_length] or "item"
    slug, n = base, 2
    while model.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


class Company(TimeStampedModel):
    class Size(models.TextChoices):
        S1 = "1-10"
        S2 = "11-50"
        S3 = "51-200"
        S4 = "201-1000"
        S5 = "1000+"

    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=160, blank=True)
    industry = models.CharField(max_length=120, blank=True)
    size = models.CharField(max_length=10, choices=Size.choices, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="company-logos/", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Company, self.name)
        super().save(*args, **kwargs)


class CompanyMember(TimeStampedModel):
    """People who act for a company. Admins manage the page and the team; recruiters post jobs."""

    class Role(models.TextChoices):
        ADMIN = "admin"
        RECRUITER = "recruiter"

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company_roles"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.RECRUITER)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "user"], name="company_member_once")
        ]


class CompanyFollower(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="followers")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followed_companies"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "user"], name="company_follow_once")
        ]


class CompanyUpdate(TimeStampedModel):
    """News from a company's team: shown on its page and to the people who follow it."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="updates")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    body = models.TextField(max_length=3000)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["company", "-created_at"], name="company_update_idx")]


class Job(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft"
        OPEN = "open"
        CLOSED = "closed"

    class Workplace(models.TextChoices):
        ONSITE = "onsite", "On site"
        HYBRID = "hybrid", "Hybrid"
        REMOTE = "remote", "Remote"

    class Type(models.TextChoices):
        FULL_TIME = "full_time", "Full time"
        PART_TIME = "part_time", "Part time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"

    class Level(models.TextChoices):
        ENTRY = "entry", "Entry"
        MID = "mid", "Mid"
        SENIOR = "senior", "Senior"
        LEAD = "lead", "Lead"

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="jobs")
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    title = models.CharField(max_length=160)
    description = models.TextField()
    location = models.CharField(max_length=160, blank=True)
    workplace = models.CharField(max_length=10, choices=Workplace.choices, default=Workplace.ONSITE)
    employment_type = models.CharField(max_length=12, choices=Type.choices, default=Type.FULL_TIME)
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.MID)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    skills = models.ManyToManyField("profiles.Skill", blank=True, related_name="jobs")
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    closes_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"], name="job_status_published_idx")
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(salary_min__isnull=True)
                | models.Q(salary_max__isnull=True)
                | models.Q(salary_max__gte=models.F("salary_min")),
                name="job_salary_band_ordered",
            )
        ]

    def __str__(self):
        return f"{self.title} at {self.company}"


class SavedJob(TimeStampedModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saves")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_jobs"
    )

    class Meta:
        constraints = [models.UniqueConstraint(fields=["job", "user"], name="save_job_once")]


def resume_path(instance, filename):
    # Random names: a résumé URL must not be guessable even if storage is ever made public.
    return f"resumes/{uuid.uuid4().hex}.pdf"


class Application(TimeStampedModel):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        REVIEWING = "reviewing", "In review"
        INTERVIEW = "interview", "Interviewing"
        OFFER = "offer", "Offer"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Not selected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    resume = models.FileField(upload_to=resume_path, validators=[FileExtensionValidator(["pdf"])])
    cover_letter = models.TextField(blank=True, max_length=5000)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUBMITTED)
    status_changed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["job", "applicant"], name="apply_once_per_job")
        ]

    def __str__(self):
        return f"{self.applicant_id} → {self.job_id} ({self.status})"


class Interview(TimeStampedModel):
    """An interview slot the hiring team offers; the candidate confirms or declines it."""

    class Kind(models.TextChoices):
        VIDEO = "video", "Video call"
        PHONE = "phone", "Phone call"
        ONSITE = "onsite", "On site"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Awaiting reply"
        CONFIRMED = "confirmed", "Confirmed"
        DECLINED = "declined", "Declined"
        CANCELLED = "cancelled", "Cancelled"

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="interviews"
    )
    scheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    starts_at = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=45)
    kind = models.CharField(max_length=8, choices=Kind.choices, default=Kind.VIDEO)
    location = models.CharField(max_length=300, help_text="Meeting link, phone number or address")
    details = models.TextField(blank=True, max_length=2000)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SCHEDULED)
    response_note = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["starts_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_minutes__gte=15, duration_minutes__lte=240),
                name="interview_duration_range",
            )
        ]

    def __str__(self):
        return f"interview {self.application_id} at {self.starts_at:%Y-%m-%d %H:%M}"
