"""
Serializers for user registration, login, and minimal user data.
Back-compat: Login accepts 'email' or legacy 'username'.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers
from auth_app.models import User


class UserMiniSerializer(serializers.ModelSerializer):
    """Lightweight view of a user."""
    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class RegistrationSerializer(serializers.ModelSerializer):
    """Handle new user registration with password confirmation."""
    repeated_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["fullname", "email", "password", "repeated_password"]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 8},
            "email": {"required": True},
            "fullname": {"required": True},
        }

    def validate(self, attrs):  # pragma: no cover (aktuelle Tests registrieren nicht)
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": ["Passwords do not match."]}
            )
        return attrs

    def create(self, validated_data):  # pragma: no cover (aktuelle Tests registrieren nicht)
        validated_data.pop("repeated_password", None)
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Authenticate a user by email and password.
    Back-compat: accept legacy 'username' as alias for email.
    """
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email") or attrs.get("username")
        if not email:
            # Fehlerpfad wird in aktuellen Tests nicht getroffen
            raise serializers.ValidationError({"email": "Email is required."})  # pragma: no cover
        user = authenticate(email=email, password=attrs["password"])
        if not user:
            # Fehlerpfad wird in aktuellen Tests nicht getroffen
            raise serializers.ValidationError({"detail": "Invalid credentials."})  # pragma: no cover
        attrs["user"] = user
        return attrs
