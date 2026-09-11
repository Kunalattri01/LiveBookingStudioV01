from django.contrib.auth import get_user_model
from django.test import TestCase


class AccountTests(TestCase):
    def test_register_page_creates_user(self):
        response = self.client.post("/accounts/register/", {
            "email": "person@example.com",
            "first_name": "Test",
            "last_name": "Person",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(email="person@example.com").exists())

    def test_api_registration_creates_profile(self):
        response = self.client.post("/api/v1/accounts/register/", {
            "username": "api-person",
            "email": "api@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(username="api-person")
        self.assertTrue(hasattr(user, "profile"))

    def test_login_api_accepts_email(self):
        User = get_user_model()
        User.objects.create_user(username="person", email="person@example.com", password="StrongPass123!")
        response = self.client.post("/api/v1/accounts/login/", {
            "username_or_email": "person@example.com",
            "password": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 200)
