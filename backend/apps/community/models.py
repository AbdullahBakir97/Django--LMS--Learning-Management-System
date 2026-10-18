from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


class Group(TimeStampedModel):
    class Privacy(models.TextChoices):
        PUBLIC = "public", "Public: anyone can see posts and join"
        PRIVATE = "private", "Private: members only, joining needs approval"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    privacy = models.CharField(max_length=10, choices=Privacy.choices, default=Privacy.PUBLIC)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_groups"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:120] or "group"
            slug, n = base, 2
            while Group.objects.filter(slug=slug).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)


class Membership(TimeStampedModel):
    class Role(models.TextChoices):
        OWNER = "owner"
        ADMIN = "admin"
        MEMBER = "member"

    class Status(models.TextChoices):
        ACTIVE = "active"
        PENDING = "pending"

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_memberships"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["group", "user"], name="membership_once")]
        indexes = [models.Index(fields=["group", "status"], name="membership_group_status_idx")]

    def __str__(self):
        return f"{self.user_id} in {self.group_id} ({self.role}, {self.status})"

    @property
    def can_manage(self) -> bool:
        return self.status == self.Status.ACTIVE and self.role in (self.Role.OWNER, self.Role.ADMIN)


class Post(TimeStampedModel):
    """A post on your profile (group empty) or in a group. Plain text; links stay as typed."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    group = models.ForeignKey(
        Group, null=True, blank=True, on_delete=models.CASCADE, related_name="posts"
    )
    body = models.TextField(max_length=5000)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["author", "-created_at"], name="post_author_idx")]

    def __str__(self):
        return f"post {self.pk} by {self.author_id}"


class Event(TimeStampedModel):
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hosted_events"
    )
    group = models.ForeignKey(
        Group, null=True, blank=True, on_delete=models.CASCADE, related_name="events"
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    online_url = models.URLField(blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["starts_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")), name="event_ends_after_start"
            )
        ]

    def __str__(self):
        return self.title


class Attendance(TimeStampedModel):
    class Status(models.TextChoices):
        GOING = "going"
        INTERESTED = "interested"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="attendances")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendances"
    )
    status = models.CharField(max_length=12, choices=Status.choices)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "user"], name="attend_once")]

    def __str__(self):
        return f"{self.user_id} {self.status} {self.event_id}"
