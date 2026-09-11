from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Notification


class CoreTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="core-user",
            password="StrongPass123!",
        )

    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["database"])

    def test_notification_is_private_to_user(self):
        other = get_user_model().objects.create_user(
            username="other-user", password="StrongPass123!"
        )
        Notification.objects.create(user=self.user, title="Mine", message="Private")
        Notification.objects.create(user=other, title="Other", message="Private")
        self.client.force_login(self.user)
        response = self.client.get("/api/v1/core/notifications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "Mine")
