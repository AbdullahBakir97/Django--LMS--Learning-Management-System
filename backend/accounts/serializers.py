from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Returned by /api/auth/user/ and embedded in profiles."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "date_joined"]
        read_only_fields = ["id", "username", "email", "role", "date_joined"]
