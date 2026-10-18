from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.engagement.serializers import AuthorSerializer, ReactionSummarySerializer

from .models import Attendance, Event, EventFeedback, Group, Membership, Post, PostImage


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


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ["image", "width", "height"]


class SharedPostSerializer(serializers.ModelSerializer):
    """The original inside a share: enough to show it, without its own counters.

    Hidden once its group is not public, since the share is seen by people outside it.
    """

    def to_representation(self, post):
        if post.group_id and post.group.privacy != Group.Privacy.PUBLIC:
            return None
        return super().to_representation(post)

    author = AuthorSerializer(read_only=True)
    group = GroupRefSerializer(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ["id", "author", "group", "body", "images", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    group = GroupRefSerializer(read_only=True)
    group_slug = serializers.SlugField(write_only=True, required=False, allow_null=True)
    edited = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    images = PostImageSerializer(many=True, read_only=True)
    shared_from = SharedPostSerializer(read_only=True)
    share_count = serializers.IntegerField(read_only=True, default=0)

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
            "images",
            "shared_from",
            "share_count",
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
        managed = self.context.get("managed_groups")
        if managed is None:
            from .services import can_moderate_post

            return can_moderate_post(self.context["request"].user, obj)
        user = self.context["request"].user
        return obj.author_id == user.id or user.role == "admin" or obj.group_id in managed


class PostWriteSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000, allow_blank=True, default="")
    group_slug = serializers.SlugField(required=False, allow_null=True)
    images = serializers.ListField(child=serializers.FileField(), required=False, default=list)


class PostEditSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000)


class ShareSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000, allow_blank=True, required=False, default="")


class EventSerializer(serializers.ModelSerializer):
    host = AuthorSerializer(read_only=True)
    group = GroupRefSerializer(read_only=True)
    group_slug = serializers.SlugField(write_only=True, required=False, allow_null=True)
    going_count = serializers.IntegerField(read_only=True, default=0)
    my_status = serializers.CharField(read_only=True, default=None, allow_null=True)
    can_edit = serializers.SerializerMethodField()
    rating = serializers.FloatField(read_only=True, default=None, allow_null=True)
    rating_count = serializers.IntegerField(read_only=True, default=0)
    my_rating = serializers.IntegerField(read_only=True, default=None, allow_null=True)

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
            "rating",
            "rating_count",
            "my_rating",
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


class FeedbackSerializer(serializers.ModelSerializer):
    person = AuthorSerializer(source="user", read_only=True)

    class Meta:
        model = EventFeedback
        fields = ["person", "rating", "comment", "created_at"]
        read_only_fields = ["person", "created_at"]
        extra_kwargs = {"rating": {"min_value": 1, "max_value": 5}}


class RsvpSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Attendance.Status.choices)
