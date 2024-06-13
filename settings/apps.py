from django.apps import AppConfig


class SettingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "settings"
    
    def ready(self):
        import settings.signals
