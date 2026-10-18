from django.apps import AppConfig


class DemoConfig(AppConfig):
    """Tooling, not a context: `manage.py seed_demo` fills a fresh database to explore."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.demo"
