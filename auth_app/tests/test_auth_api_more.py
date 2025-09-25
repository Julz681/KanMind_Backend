"""
API tests aligned with the current auth endpoints.
- Validates short password handling on registration.
- Verifies email-check returns 404 before registration and 200 after.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class AuthApiMoreTests(APITestCase):
    def test_registration_validation_short_password(self):
        """Registration must reject passwords shorter than 8 chars."""
        payload = {
            "fullname": "Short Pw",
            "email": "s@example.com",
            "password": "123",
            "repeated_password": "123",
        }
        res = self.client.post("/api/auth/registration/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", res.data)

    def test_email_check_not_found_then_found(self):
        """Email check returns 404 before user exists, 200 after registration."""
        email = "guest@test.de"
        res1 = self.client.get("/api/auth/email-check/", {"email": email})
        self.assertEqual(res1.status_code, status.HTTP_404_NOT_FOUND)

        reg = {
            "fullname": "Guest",
            "email": email,
            "password": "guest1234",
            "repeated_password": "guest1234",
        }
        res2 = self.client.post("/api/auth/registration/", reg, format="json")
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

        res3 = self.client.get("/api/auth/email-check/", {"email": email})
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        self.assertEqual(res3.data["email"], email)

        self.assertTrue(get_user_model().objects.filter(email=email).exists())
