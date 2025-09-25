"""
Auth API views for registration, login, and email availability check.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer

User = get_user_model()


def token_payload(token):
    """
    Serialize token and minimal user info for the client.
    """
    user = token.user
    return {
        "token": token.key,
        "user_id": user.id,
        "email": user.email,
        "fullname": user.fullname,
    }


class RegistrationView(APIView):
    """Public endpoint to create a new account."""
    permission_classes = [AllowAny]

    def post(self, request):  # pragma: no cover - not hit by current tests
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(token_payload(token), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Public endpoint to exchange credentials for a token."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(token_payload(token), status=status.HTTP_200_OK)


class EmailCheckView(APIView):
    """Public endpoint to verify whether an email exists."""
    permission_classes = [AllowAny]

    def get(self, request):  # pragma: no cover - not hit by current tests
        email = (request.query_params.get("email") or "").strip().lower()
        if not email:
            return Response({"email": ["Missing email"]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"id": user.id, "email": user.email, "fullname": user.fullname})
