"""
Serializers for user registration, login, and minimal user data.
Back-compat: Login accepts 'email' or legacy 'username'.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from auth_app.models import User


class UserMiniSerializer(serializers.ModelSerializer):
    """Lightweight view of a user."""
    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Handle new user registration with password confirmation.
    - Validates unique email (returns 400 with clear message instead of 500)
    - Ensures passwords match
    """
    repeated_password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="This email is already registered.",
            )
        ],
    )

    class Meta:
        model = User
        fields = ["fullname", "email", "password", "repeated_password"]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 8},
            "fullname": {"required": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": ["Passwords do not match."]}
            )
        return attrs

    def create(self, validated_data):
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
            raise serializers.ValidationError({"email": "Email is required."})
        user = authenticate(email=email, password=attrs["password"])
        if not user:
            raise serializers.ValidationError({"detail": "Invalid credentials."})
        attrs["user"] = user
        return attrs
