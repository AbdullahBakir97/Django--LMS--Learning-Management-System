from rest_framework import serializers

from .models import Connection


class PersonSerializer(serializers.Serializer):
    """A compact card: enough to render a name, a face and a headline."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.SerializerMethodField()
    headline = serializers.CharField(source="profile.headline", default="")
    avatar = serializers.ImageField(source="profile.avatar", default=None)
    role = serializers.CharField()

    def get_name(self, user) -> str:
        return user.get_full_name() or user.username


class FollowerSerializer(serializers.Serializer):
    person = PersonSerializer(source="follower")
    since = serializers.DateTimeField(source="created_at")


class FollowingSerializer(serializers.Serializer):
    person = PersonSerializer(source="following")
    since = serializers.DateTimeField(source="created_at")


class SuggestionSerializer(PersonSerializer):
    shared_skills = serializers.IntegerField()


class ConnectionSerializer(serializers.ModelSerializer):
    person = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()

    class Meta:
        model = Connection
        fields = ["id", "status", "direction", "person", "created_at", "accepted_at"]

    def _viewer(self):
        return self.context["request"].user

    def get_person(self, obj) -> dict:
        return PersonSerializer(obj.other(self._viewer()), context=self.context).data

    def get_direction(self, obj) -> str:
        return "outgoing" if obj.requester_id == self._viewer().id else "incoming"


class ConnectRequestSerializer(serializers.Serializer):
    username = serializers.CharField()


class RelationshipSerializer(serializers.Serializer):
    following = serializers.BooleanField()
    followed_by = serializers.BooleanField()
    followers = serializers.IntegerField()
    following_count = serializers.IntegerField()
    connections = serializers.IntegerField()
    connection = serializers.DictField(allow_null=True)
