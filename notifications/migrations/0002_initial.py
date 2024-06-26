# Generated by Django 5.0.6 on 2024-06-13 20:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("activity", "0002_initial"),
        ("notifications", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="recipient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications_recipient",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="shares",
            field=models.ManyToManyField(
                blank=True, related_name="notifications_shares", to="activity.share"
            ),
        ),
        migrations.AddField(
            model_name="notificationreadstatus",
            name="notification",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="notifications.notification",
            ),
        ),
        migrations.AddField(
            model_name="notificationreadstatus",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="notificationsettings",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="notificationtemplate",
            name="notification_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="notifications.notificationtype",
            ),
        ),
        migrations.AddField(
            model_name="notificationsettings",
            name="notification_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="notifications.notificationtype",
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="notification_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="notifications.notificationtype",
            ),
        ),
    ]
