from django.apps import AppConfig


class EngagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.engagement"

    def ready(self):
        from . import targets  # noqa: F401  registers comments as a reaction target
