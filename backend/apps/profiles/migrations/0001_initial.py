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
            name="Skill",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("headline", models.CharField(blank=True, max_length=160)),
                ("bio", models.TextField(blank=True)),
                ("avatar", models.ImageField(blank=True, upload_to="avatars/")),
                ("location", models.CharField(blank=True, max_length=120)),
                ("website", models.URLField(blank=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Experience",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("description", models.TextField(blank=True)),
                ("title", models.CharField(max_length=160)),
                ("company", models.CharField(max_length=160)),
                ("location", models.CharField(blank=True, max_length=120)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="experiences", to="profiles.profile")),
            ],
            options={
                "ordering": ["-start_date", "-created_at"],
                "abstract": False,
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("end_date__isnull", True), ("end_date__gte", models.F("start_date")), _connector="OR"), name="experience_end_after_start"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Education",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("description", models.TextField(blank=True)),
                ("institution", models.CharField(max_length=160)),
                ("degree", models.CharField(blank=True, max_length=160)),
                ("field_of_study", models.CharField(blank=True, max_length=160)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="educations", to="profiles.profile")),
            ],
            options={
                "ordering": ["-start_date", "-created_at"],
                "abstract": False,
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("end_date__isnull", True), ("end_date__gte", models.F("start_date")), _connector="OR"), name="education_end_after_start"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ProfileSkill",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("level", models.CharField(choices=[("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced"), ("expert", "Expert")], default="intermediate", max_length=16)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="skills", to="profiles.profile")),
                ("skill", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="profile_skills", to="profiles.skill")),
            ],
            options={
                "ordering": ["-created_at"],
                "constraints": [models.UniqueConstraint(fields=("profile", "skill"), name="profileskill_unique")],
            },
        ),
        migrations.CreateModel(
            name="Endorsement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("endorsed_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="endorsements_given", to=settings.AUTH_USER_MODEL)),
                ("profile_skill", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="endorsements", to="profiles.profileskill")),
            ],
            options={
                "ordering": ["-created_at"],
                "constraints": [models.UniqueConstraint(fields=("profile_skill", "endorsed_by"), name="endorsement_unique")],
            },
        ),
    ]
