import json

from django.test import TestCase
from django.urls import reverse


class PublicPagesSmokeTests(TestCase):
    def test_login_page_ok(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)

    def test_forgot_password_page_ok(self):
        resp = self.client.get(reverse("forgot_password"))
        self.assertEqual(resp.status_code, 200)

    def test_reset_password_page_ok(self):
        resp = self.client.get(reverse("reset_password", args=["dummy", "dummy-token"]))
        self.assertEqual(resp.status_code, 200)


class ApiStatusSmokeTests(TestCase):
    def test_forgot_password_returns_ok_even_for_unknown_user(self):
        payload = {"identifier": "unknown@example.com"}
        resp = self.client.post(
            reverse("api_forgot_password"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("ok"))

    def test_reset_password_validation_errors_for_invalid_link(self):
        payload = {
            "uidb64": "invalid",
            "token": "invalid",
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        }
        resp = self.client.post(
            reverse("api_reset_password"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())
