from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Comment, Reaction


class AuthorSerializer(serializers.Serializer):
    username = serializers.CharField()
    name = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source="profile.avatar", default=None)

    def get_name(self, user) -> str:
        return user.get_full_name() or user.username


class ReactionSummarySerializer(serializers.Serializer):
    counts = serializers.DictField(child=serializers.IntegerField())
    mine = serializers.ChoiceField(choices=Reaction.Kind.choices, allow_null=True)


class ReplySerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    edited = serializers.SerializerMethodField()
    deleted = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "body",
            "parent",
            "edited",
            "deleted",
            "created_at",
            "reactions",
            "can_edit",
            "can_delete",
        ]

    def get_edited(self, obj) -> bool:
        return obj.edited_at is not None

    def get_deleted(self, obj) -> bool:
        return obj.deleted_at is not None

    @extend_schema_field(ReactionSummarySerializer)
    def get_reactions(self, obj) -> dict:
        return self.context.get("reactions", {}).get(obj.id, {"counts": {}, "mine": None})

    def _user(self):
        return self.context["request"].user

    def get_can_edit(self, obj) -> bool:
        return obj.deleted_at is None and obj.author_id == self._user().id

    def get_can_delete(self, obj) -> bool:
        return obj.deleted_at is None and (
            obj.author_id == self._user().id or self.context.get("moderator", False)
        )


class CommentSerializer(ReplySerializer):
    replies = ReplySerializer(many=True, read_only=True)

    class Meta(ReplySerializer.Meta):
        fields = [*ReplySerializer.Meta.fields, "replies"]


class CommentWriteSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000, trim_whitespace=True)
    parent = serializers.IntegerField(required=False, allow_null=True)


class ReactionWriteSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=Reaction.Kind.choices)
