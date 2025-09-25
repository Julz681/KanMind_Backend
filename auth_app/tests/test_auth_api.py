"""
API tests for the current authentication endpoints.
Covers registration, login, and email-check functionality.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class AuthApiTests(APITestCase):
    def test_registration_creates_user_and_returns_token(self):
        """
        Registration should create a new user and return an auth token.
        """
        payload = {
            "fullname": "Kevin",
            "email": "k@example.com",
            "password": "test1234",
            "repeated_password": "test1234",
        }
        res = self.client.post("/api/auth/registration/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", res.data)
        self.assertIn("user_id", res.data)
        self.assertTrue(
            get_user_model().objects.filter(email="k@example.com").exists()
        )

    def test_login_returns_token(self):
        """
        Login should return a token for a valid email/password combination.
        """
        user_model = get_user_model()
        user_model.objects.create_user(
            email="u1@example.com",
            fullname="User One",
            password="p1test123",
        )
        payload = {"email": "u1@example.com", "password": "p1test123"}
        res = self.client.post("/api/auth/login/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("token", res.data)
        self.assertEqual(res.data["email"], "u1@example.com")

    def test_email_check_returns_404_then_200(self):
        """
        Email check should return 404 before registration and 200 after.
        """
        email = "guest@example.com"
        res1 = self.client.get("/api/auth/email-check/", {"email": email})
        self.assertEqual(res1.status_code, status.HTTP_404_NOT_FOUND)

        reg_payload = {
            "fullname": "Guest",
            "email": email,
            "password": "guestpass123",
            "repeated_password": "guestpass123",
        }
        self.client.post("/api/auth/registration/", reg_payload, format="json")

        res2 = self.client.get("/api/auth/email-check/", {"email": email})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["email"], email)
