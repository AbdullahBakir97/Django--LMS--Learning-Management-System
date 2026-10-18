from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.messaging"

    def ready(self):
        from apps.core.realtime import on_client_message

        from . import services

        @on_client_message("typing")
        def typing(user, payload):
            conversation = payload.get("conversation")
            if isinstance(conversation, int):
                services.typing(user, conversation)
