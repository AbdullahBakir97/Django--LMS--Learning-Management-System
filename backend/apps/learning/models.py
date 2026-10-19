import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


def default_currency() -> str:
    return settings.PAYMENTS_CURRENCY


class Course(TimeStampedModel):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="courses_taught"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    summary = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    cover = models.ImageField(upload_to="courses/covers/", blank=True)
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.BEGINNER)
    language = models.CharField(max_length=8, default="en")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    # In the currency's smallest unit (cents). 0 is a free course.
    price_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default=default_currency)
    published_at = models.DateTimeField(null=True, blank=True)
    prerequisites = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="unlocks"
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [models.Index(fields=["status", "level"], name="course_status_level_idx")]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "course"
            self.slug = base
            n = 2
            while Course.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base}-{n}"
                n += 1
        super().save(*args, **kwargs)

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED

    @property
    def is_paid(self) -> bool:
        return self.price_cents > 0


class Lesson(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()
    content = models.TextField(blank=True, help_text="Markdown")
    video_url = models.URLField(blank=True)
    is_free_preview = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["course", "order"], name="lesson_order_unique")
        ]

    def __str__(self):
        return f"{self.course.title} · {self.order}. {self.title}"


class LessonAttachment(TimeStampedModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="attachments")
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="courses/attachments/")

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.title


class Quiz(TimeStampedModel):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name="quiz")
    title = models.CharField(max_length=200)
    pass_score = models.PositiveSmallIntegerField(default=70, help_text="Percent needed to pass")

    class Meta:
        ordering = ["lesson__order"]

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["quiz", "order"], name="question_order_unique")
        ]

    def __str__(self):
        return self.text[:60]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text


class Enrollment(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["course", "student"], name="enrollment_unique")
        ]

    def __str__(self):
        return f"{self.student} in {self.course}"


class LessonProgress(TimeStampedModel):
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["enrollment", "lesson"], name="lesson_progress_unique")
        ]

    def __str__(self):
        return f"{self.enrollment} · {self.lesson_id}"


class QuizAttempt(TimeStampedModel):
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveSmallIntegerField(help_text="Percent")
    passed = models.BooleanField()
    answers = models.JSONField(default=dict, help_text="question id -> chosen choice id")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.enrollment} · {self.quiz} · {self.score}%"


class Certificate(TimeStampedModel):
    enrollment = models.OneToOneField(
        Enrollment, on_delete=models.CASCADE, related_name="certificate"
    )
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    pdf = models.FileField(upload_to="certificates/", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.code)
