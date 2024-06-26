# Generated by Django 5.0.6 on 2024-06-13 20:18

import django.db.models.deletion
import taggit.managers
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("activity", "0003_initial"),
        ("events", "0001_initial"),
        ("profiles", "0001_initial"),
        (
            "taggit",
            "0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="attendees",
            field=models.ManyToManyField(
                blank=True, related_name="events", to="profiles.userprofile"
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="categories",
            field=models.ManyToManyField(
                related_name="events_categoories", to="activity.category"
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="organizer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="organized_events",
                to="profiles.userprofile",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="tags",
            field=taggit.managers.TaggableManager(
                help_text="A comma-separated list of tags.",
                through="taggit.TaggedItem",
                to="taggit.Tag",
                verbose_name="Tags",
            ),
        ),
    ]
