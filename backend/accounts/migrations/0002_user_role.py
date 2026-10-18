from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[("learner", "Learner"), ("instructor", "Instructor"), ("admin", "Admin")],
                default="learner",
                max_length=16,
            ),
        ),
    ]
