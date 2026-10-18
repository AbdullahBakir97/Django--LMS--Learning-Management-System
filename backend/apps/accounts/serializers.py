from dj_rest_auth.registration.serializers import RegisterSerializer as DefaultRegisterSerializer
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Returned by /api/auth/user/ and embedded in profiles."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "date_joined"]
        read_only_fields = ["id", "username", "email", "role", "date_joined"]


class PublicUserSerializer(UserSerializer):
    """Someone else's account, as shown on their profile: no email address."""

    class Meta(UserSerializer.Meta):
        fields = [f for f in UserSerializer.Meta.fields if f != "email"]
        read_only_fields = fields


class RegisterSerializer(DefaultRegisterSerializer):
    """allauth only rejects emails with a *verified* address row; reject any existing user."""

    def validate_email(self, email):
        email = super().validate_email(email)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user is already registered with this email.")
        return email
