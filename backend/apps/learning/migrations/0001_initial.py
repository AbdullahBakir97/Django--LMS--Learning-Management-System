import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("summary", models.CharField(blank=True, max_length=300)),
                ("description", models.TextField(blank=True)),
                ("cover", models.ImageField(blank=True, upload_to="courses/covers/")),
                ("level", models.CharField(choices=[("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced")], default="beginner", max_length=16)),
                ("language", models.CharField(default="en", max_length=8)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], default="draft", max_length=16)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("instructor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="courses_taught", to=settings.AUTH_USER_MODEL)),
                ("prerequisites", models.ManyToManyField(blank=True, related_name="unlocks", to="learning.course")),
            ],
            options={
                "ordering": ["-published_at", "-created_at"],
                "indexes": [models.Index(fields=["status", "level"], name="course_status_level_idx")],
            },
        ),
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("order", models.PositiveIntegerField()),
                ("content", models.TextField(blank=True, help_text="Markdown")),
                ("video_url", models.URLField(blank=True)),
                ("is_free_preview", models.BooleanField(default=False)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="learning.course")),
            ],
            options={
                "ordering": ["order"],
                "constraints": [models.UniqueConstraint(fields=("course", "order"), name="lesson_order_unique")],
            },
        ),
        migrations.CreateModel(
            name="LessonAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("file", models.FileField(upload_to="courses/attachments/")),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="learning.lesson")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="Quiz",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("pass_score", models.PositiveSmallIntegerField(default=70, help_text="Percent needed to pass")),
                ("lesson", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="quiz", to="learning.lesson")),
            ],
            options={"ordering": ["lesson__order"]},
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField()),
                ("order", models.PositiveIntegerField()),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="learning.quiz")),
            ],
            options={
                "ordering": ["order"],
                "constraints": [models.UniqueConstraint(fields=("quiz", "order"), name="question_order_unique")],
            },
        ),
        migrations.CreateModel(
            name="Choice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.CharField(max_length=300)),
                ("is_correct", models.BooleanField(default=False)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="choices", to="learning.question")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("completed", "Completed")], default="active", max_length=16)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="learning.course")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
                "constraints": [models.UniqueConstraint(fields=("course", "student"), name="enrollment_unique")],
            },
        ),
        migrations.CreateModel(
            name="LessonProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("enrollment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lesson_progress", to="learning.enrollment")),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress", to="learning.lesson")),
            ],
            options={
                "constraints": [models.UniqueConstraint(fields=("enrollment", "lesson"), name="lesson_progress_unique")],
            },
        ),
        migrations.CreateModel(
            name="QuizAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("score", models.PositiveSmallIntegerField(help_text="Percent")),
                ("passed", models.BooleanField()),
                ("answers", models.JSONField(default=dict, help_text="question id -> chosen choice id")),
                ("enrollment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quiz_attempts", to="learning.enrollment")),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="learning.quiz")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Certificate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("pdf", models.FileField(blank=True, upload_to="certificates/")),
                ("enrollment", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="certificate", to="learning.enrollment")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
