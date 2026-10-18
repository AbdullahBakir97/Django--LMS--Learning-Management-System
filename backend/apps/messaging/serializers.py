from rest_framework import serializers

from apps.engagement.serializers import AuthorSerializer

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender = AuthorSerializer(allow_null=True)
    body = serializers.SerializerMethodField()
    edited = serializers.SerializerMethodField()
    deleted = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "body", "edited", "deleted", "created_at"]

    def get_body(self, obj) -> str:
        return "" if obj.deleted_at else obj.body

    def get_edited(self, obj) -> bool:
        return obj.edited_at is not None

    def get_deleted(self, obj) -> bool:
        return obj.deleted_at is not None


class ConversationSerializer(serializers.ModelSerializer):
    people = serializers.SerializerMethodField()
    unread = serializers.IntegerField(read_only=True, default=0)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "title", "is_group", "people", "unread", "last_message", "last_message_at"]

    def get_people(self, obj) -> list[dict]:
        """Everyone but you; for a direct conversation that is the other person."""
        me = self.context["request"].user.id
        others = [p.user for p in obj.participants.all() if p.user_id != me]
        return AuthorSerializer(others, many=True).data

    def get_last_message(self, obj) -> dict | None:
        last = self.context.get("last_messages", {}).get(getattr(obj, "last_message_id", None))
        return MessageSerializer(last).data if last else None


class StartSerializer(serializers.Serializer):
    usernames = serializers.ListField(child=serializers.CharField(), min_length=1, max_length=19)
    title = serializers.CharField(required=False, allow_blank=True, max_length=120)
    body = serializers.CharField(required=False, allow_blank=True, max_length=4000)


class MessageWriteSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=4000)
