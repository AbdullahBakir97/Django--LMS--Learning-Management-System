from zoneinfo import available_timezones

from rest_framework import serializers

from .models import Notification, Preference


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "kind", "title", "body", "url", "actor", "read", "created_at"]

    def get_actor(self, obj) -> dict | None:
        if obj.actor is None:
            return None
        return {"username": obj.actor.username, "name": obj.actor.get_full_name()}

    def get_read(self, obj) -> bool:
        return obj.read_at is not None


class PreferenceSerializer(serializers.ModelSerializer):
    muted_kinds = serializers.ListField(
        child=serializers.ChoiceField(choices=Notification.Kind.choices), required=False
    )
    kinds = serializers.SerializerMethodField()

    class Meta:
        model = Preference
        fields = [
            "email_enabled",
            "muted_kinds",
            "digest",
            "quiet_start",
            "quiet_end",
            "timezone",
            "kinds",
        ]

    def get_kinds(self, obj) -> list[dict]:
        return [{"value": v, "label": label} for v, label in Notification.Kind.choices]

    def validate_muted_kinds(self, value):
        return sorted(set(value))

    def validate_timezone(self, value):
        if value not in available_timezones():
            raise serializers.ValidationError("Unknown time zone.")
        return value

    def validate(self, attrs):
        start = attrs.get("quiet_start", getattr(self.instance, "quiet_start", None))
        end = attrs.get("quiet_end", getattr(self.instance, "quiet_end", None))
        if (start is None) != (end is None):
            raise serializers.ValidationError(
                {"quiet_end": "Set both ends of quiet hours, or neither."}
            )
        return attrs
