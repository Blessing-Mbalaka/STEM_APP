from datetime import timedelta

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import ClassSession, Course, CustomUser, Message, Reservation


class PaidClassAccessTests(TestCase):
    def setUp(self):
        self.tutor = CustomUser.objects.create_user("tutor", password="pass", is_tutor=True, languages=["English"])
        self.student = CustomUser.objects.create_user("student", password="pass", email="student@example.com")
        self.course = Course.objects.create(title="Paid class test")
        start = timezone.now() + timedelta(days=1)
        self.session = ClassSession.objects.create(
            course=self.course, title="Algebra", starts_at=start,
            ends_at=start + timedelta(hours=1), created_by=self.tutor,
            price="150.00", language="English", location="https://example.com/private",
        )

    def test_paid_link_is_withheld_until_tutor_approves(self):
        self.client.force_login(self.student)
        reserve = self.client.post(reverse("api_class_reserve", args=[self.session.pk]))
        self.assertEqual(reserve.status_code, 200)
        reservation = Reservation.objects.get(user=self.student, session=self.session)
        self.assertEqual(reservation.payment_status, "pending")
        self.assertEqual(self.client.get(reverse("api_classes_list")).json()["results"][0]["location"], "")

        self.client.force_login(self.tutor)
        response = self.client.patch(
            reverse("api_tutor_payment_request_detail", args=[reservation.pk]),
            data='{"payment_status":"approved"}', content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        notification = Message.objects.get(recipient=self.student, related_session=self.session)
        self.assertEqual(notification.sender.username, "stem-lms-system")
        self.assertIn("Payment received", notification.subject)
        self.assertIn("https://example.com/private", notification.body)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Payment received", mail.outbox[0].subject)

        self.client.force_login(self.student)
        result = self.client.get(reverse("api_classes_list")).json()["results"][0]
        self.assertEqual(result["location"], "https://example.com/private")

    def test_approving_twice_does_not_duplicate_system_message(self):
        reservation = Reservation.objects.create(user=self.student, session=self.session, payment_status="pending")
        self.client.force_login(self.tutor)
        url = reverse("api_tutor_payment_request_detail", args=[reservation.pk])
        for _ in range(2):
            self.assertEqual(self.client.patch(url, data='{"payment_status":"approved"}', content_type="application/json").status_code, 200)
        self.assertEqual(Message.objects.filter(recipient=self.student, related_session=self.session).count(), 1)

    def test_other_tutor_cannot_release_payment(self):
        other = CustomUser.objects.create_user("other", password="pass", is_tutor=True)
        reservation = Reservation.objects.create(user=self.student, session=self.session, payment_status="pending")
        self.client.force_login(other)
        response = self.client.patch(
            reverse("api_tutor_payment_request_detail", args=[reservation.pk]),
            data='{"payment_status":"approved"}', content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_class_payload_marks_payment_proof_as_sent(self):
        Reservation.objects.create(user=self.student, session=self.session, payment_status="pending")
        Message.objects.create(
            sender=self.student,
            recipient=self.tutor,
            subject="Payment proof",
            body="Attached",
            related_session=self.session,
            attachment=SimpleUploadedFile("proof.pdf", b"proof", content_type="application/pdf"),
        )
        self.client.force_login(self.student)
        result = self.client.get(reverse("api_classes_list")).json()["results"][0]
        self.assertTrue(result["proof_sent"])
