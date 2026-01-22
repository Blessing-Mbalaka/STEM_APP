import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core import mail
from django.conf import settings
from unittest.mock import patch

User = get_user_model()


class ForgotPasswordTestCase(TestCase):
    """Test the forgot password API endpoint."""

    @classmethod
    def setUpTestData(cls):
        """Create test data for the entire TestCase (once per test class)."""
        cls.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        cls.user.display_name = "Test User"
        cls.user.save()

        cls.inactive_user = User.objects.create_user(
            username="inactiveuser",
            email="inactive@example.com",
            password="testpass123",
            is_active=False
        )
        cls.inactive_user.display_name = "Inactive User"
        cls.inactive_user.save()

    def test_forgot_password_with_email(self):
        """Test forgot password with valid email."""
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["ok"], True)
        self.assertIn("reset link has been sent", data["message"])

    def test_forgot_password_with_username(self):
        """Test forgot password with valid username."""
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({"username": "testuser"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["ok"], True)

    def test_forgot_password_nonexistent_user(self):
        """Test forgot password with non-existent user (should still return ok)."""
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({"email": "nonexistent@example.com"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["ok"], True)
        # Avoid user enumeration

    def test_forgot_password_missing_identifier(self):
        """Test forgot password without email or username."""
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("Email or username required", data["error"])

    def test_forgot_password_invalid_json(self):
        """Test forgot password with invalid JSON."""
        response = self.client.post(
            "/api/auth/forgot-password",
            data="invalid json",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("Invalid JSON", data["error"])

    def test_forgot_password_case_insensitive_email(self):
        """Test forgot password with uppercase email."""
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({"email": "TEST@EXAMPLE.COM"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["ok"], True)

    def test_forgot_password_case_insensitive_username(self):
        """Test forgot password with uppercase username."""
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({"username": "TESTUSER"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["ok"], True)

    def test_forgot_password_whitespace_stripped(self):
        """Test that whitespace is stripped from email/username."""
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({"email": "  test@example.com  "}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["ok"], True)

    @patch("main.views.auth.send_mail")
    def test_forgot_password_email_sent(self, mock_send_mail):
        """Test that email is sent with reset link."""
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        # Verify send_mail was called
        self.assertTrue(mock_send_mail.called)
        call_args = mock_send_mail.call_args
        self.assertEqual(call_args[1]["subject"], "Reset your STEM LMS password")
        self.assertIn("reset-password", call_args[1]["message"])

    @patch("main.views.auth.send_mail")
    def test_forgot_password_email_failure(self, mock_send_mail):
        """Test handling of email sending failure."""
        mock_send_mail.side_effect = Exception("SMTP connection failed")
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn("Could not send reset email", data["error"])

    def test_forgot_password_inactive_user(self):
        """Test forgot password with an inactive user (should still send reset)."""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["ok"], True)

    def test_forgot_password_post_only(self):
        """Test that GET requests are not allowed."""
        response = self.client.get("/api/auth/forgot-password")
        self.assertIn(response.status_code, [405, 403])  # Method Not Allowed or Forbidden

    def test_forgot_password_with_inactive_user(self):
        """Test forgot password with an inactive user (should still send reset)."""
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({"email": "inactive@example.com"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["ok"], True)

    @patch("main.views.auth.send_mail")
    def test_forgot_password_email_sent_to_inactive_user(self, mock_send_mail):
        """Test that email is sent with reset link to inactive user."""
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({"email": "inactive@example.com"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        # Verify send_mail was called
        self.assertTrue(mock_send_mail.called)
        call_args = mock_send_mail.call_args
        self.assertEqual(call_args[1]["subject"], "Reset your STEM LMS password")
        self.assertIn("reset-password", call_args[1]["message"])