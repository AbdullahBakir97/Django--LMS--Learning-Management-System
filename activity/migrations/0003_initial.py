# Generated by Django 5.0.6 on 2024-06-13 04:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("activity", "0002_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="reaction",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="share",
            name="content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="share",
            name="shared_to",
            field=models.ManyToManyField(
                related_name="received_shares", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="share",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="thread",
            name="participants",
            field=models.ManyToManyField(
                related_name="threads", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="useractivity",
            name="categories",
            field=models.ManyToManyField(
                related_name="user_activity_categories", to="activity.category"
            ),
        ),
        migrations.AddField(
            model_name="useractivity",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="userstatistics",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
