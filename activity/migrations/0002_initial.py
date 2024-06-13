# Generated by Django 5.0.6 on 2024-06-13 04:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("activity", "0001_initial"),
        ("groups", "0001_initial"),
        ("jobs", "0001_initial"),
        ("messaging", "0001_initial"),
        ("posts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="reaction",
            name="comment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="posts.comment",
            ),
        ),
        migrations.AddField(
            model_name="reaction",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="groups.group",
            ),
        ),
        migrations.AddField(
            model_name="reaction",
            name="job_post",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="jobs.joblisting",
            ),
        ),
        migrations.AddField(
            model_name="reaction",
            name="message",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="messaging.message",
            ),
        ),
        migrations.AddField(
            model_name="reaction",
            name="post",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="posts.post",
            ),
        ),
    ]
