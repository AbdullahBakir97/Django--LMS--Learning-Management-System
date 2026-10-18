from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Profile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    headline = models.CharField(max_length=160, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    location = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.user.get_username()


class DatedEntry(TimeStampedModel):
    """An entry on a profile with a start date and an optional end date."""

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ["-start_date", "-created_at"]


class Experience(DatedEntry):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="experiences")
    title = models.CharField(max_length=160)
    company = models.CharField(max_length=160)
    location = models.CharField(max_length=120, blank=True)

    class Meta(DatedEntry.Meta):
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True)
                | models.Q(end_date__gte=models.F("start_date")),
                name="experience_end_after_start",
            )
        ]

    def __str__(self):
        return f"{self.title} at {self.company}"


class Education(DatedEntry):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="educations")
    institution = models.CharField(max_length=160)
    degree = models.CharField(max_length=160, blank=True)
    field_of_study = models.CharField(max_length=160, blank=True)

    class Meta(DatedEntry.Meta):
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True)
                | models.Q(end_date__gte=models.F("start_date")),
                name="education_end_after_start",
            )
        ]

    def __str__(self):
        return f"{self.degree} at {self.institution}".strip()


class Skill(models.Model):
    """Shared taxonomy. Per-user level lives on ProfileSkill."""

    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProfileSkill(TimeStampedModel):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        EXPERT = "expert", "Expert"

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="skills")
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name="profile_skills")
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.INTERMEDIATE)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["profile", "skill"], name="profileskill_unique")
        ]

    def __str__(self):
        return f"{self.profile} · {self.skill}"


class Endorsement(TimeStampedModel):
    profile_skill = models.ForeignKey(
        ProfileSkill, on_delete=models.CASCADE, related_name="endorsements"
    )
    endorsed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="endorsements_given"
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile_skill", "endorsed_by"], name="endorsement_unique"
            )
        ]

    def __str__(self):
        return f"{self.endorsed_by} endorses {self.profile_skill}"
