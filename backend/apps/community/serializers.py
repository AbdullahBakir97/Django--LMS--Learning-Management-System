from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.engagement.serializers import AuthorSerializer, ReactionSummarySerializer

from .models import Attendance, Event, Group, Membership, Post


class GroupSerializer(serializers.ModelSerializer):
    owner = AuthorSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True, default=0)
    my_status = serializers.CharField(read_only=True, default=None, allow_null=True)
    my_role = serializers.CharField(read_only=True, default=None, allow_null=True)

    class Meta:
        model = Group
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "privacy",
            "owner",
            "member_count",
            "my_status",
            "my_role",
            "created_at",
        ]
        read_only_fields = ["slug"]


class GroupMemberSerializer(serializers.ModelSerializer):
    person = AuthorSerializer(source="user")
    user_id = serializers.IntegerField()
    headline = serializers.CharField(source="user.profile.headline", default="")

    class Meta:
        model = Membership
        fields = ["user_id", "person", "headline", "role", "status", "created_at"]


class RoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[Membership.Role.ADMIN, Membership.Role.MEMBER])


class GroupRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["slug", "name", "privacy"]


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    group = GroupRefSerializer(read_only=True)
    group_slug = serializers.SlugField(write_only=True, required=False, allow_null=True)
    edited = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "group",
            "group_slug",
            "body",
            "edited",
            "created_at",
            "reactions",
            "comment_count",
            "can_edit",
            "can_delete",
        ]

    def get_edited(self, obj) -> bool:
        return obj.edited_at is not None

    @extend_schema_field(ReactionSummarySerializer)
    def get_reactions(self, obj) -> dict:
        return self.context.get("reactions", {}).get(obj.id, {"counts": {}, "mine": None})

    def get_comment_count(self, obj) -> int:
        return self.context.get("comment_counts", {}).get(obj.id, 0)

    def get_can_edit(self, obj) -> bool:
        return obj.author_id == self.context["request"].user.id

    def get_can_delete(self, obj) -> bool:
        from .services import can_moderate_post

        return can_moderate_post(self.context["request"].user, obj)


class PostWriteSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000)
    group_slug = serializers.SlugField(required=False, allow_null=True)


class EventSerializer(serializers.ModelSerializer):
    host = AuthorSerializer(read_only=True)
    group = GroupRefSerializer(read_only=True)
    group_slug = serializers.SlugField(write_only=True, required=False, allow_null=True)
    going_count = serializers.IntegerField(read_only=True, default=0)
    my_status = serializers.CharField(read_only=True, default=None, allow_null=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "starts_at",
            "ends_at",
            "location",
            "online_url",
            "capacity",
            "host",
            "group",
            "group_slug",
            "going_count",
            "my_status",
            "can_edit",
            "created_at",
        ]

    def get_can_edit(self, obj) -> bool:
        user = self.context["request"].user
        return obj.host_id == user.id or user.role == "admin"

    def validate(self, attrs):
        starts = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts and ends and ends <= starts:
            raise serializers.ValidationError({"ends_at": "An event ends after it starts."})
        if not attrs.get("location", getattr(self.instance, "location", "")) and not attrs.get(
            "online_url", getattr(self.instance, "online_url", "")
        ):
            raise serializers.ValidationError("Give a place or an online link.")
        return attrs


class RsvpSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Attendance.Status.choices)
