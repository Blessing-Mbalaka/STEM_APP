import json

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    CustomUser,
    CustomUserSurvey,
    CustomUserSurveyParticipant,
    CustomUserSurveyQuestion,
    CustomUserSurveyResponse,
    Game,
    GameQuestion,
)


class SurveyApiTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass",
            is_staff=True,
            is_superuser=True,
        )
        self.student = CustomUser.objects.create_user(
            username="student",
            email="student@example.com",
            password="pass",
        )

    def _json(self, response):
        return json.loads(response.content.decode("utf-8"))

    def test_admin_can_create_and_publish_survey(self):
        self.client.force_login(self.admin)
        # Create survey
        resp = self.client.post(
            reverse("api_surveys_collection"),
            data=json.dumps({"title": "Platform Pulse"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        survey_id = self._json(resp)["survey"]["id"]
        survey = CustomUserSurvey.objects.get(pk=survey_id)
        self.assertEqual(survey.title, "Platform Pulse")

        # Add question
        resp = self.client.post(
            reverse("api_survey_questions", args=[survey_id]),
            data=json.dumps(
                {
                    "prompt": "How satisfied are you?",
                    "type": "rating",
                    "isRequired": True,
                    "isScored": True,
                    "maxScore": 5,
                    "chartType": "bar",
                    "order": 1,
                    "config": {"min": 1, "max": 5, "step": 1},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        question_id = self._json(resp)["question"]["id"]
        question = CustomUserSurveyQuestion.objects.get(pk=question_id)
        self.assertTrue(question.is_required)

        # Publish survey
        resp = self.client.patch(
            reverse("api_survey_detail", args=[survey_id]),
            data=json.dumps({"isActive": True}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        survey.refresh_from_db()
        self.assertTrue(survey.is_active)

        # Student flow
        self.client.force_login(self.student)
        resp = self.client.get(reverse("api_survey_next"))
        self.assertEqual(resp.status_code, 200)
        payload = self._json(resp)
        self.assertIsNotNone(payload["survey"])
        self.assertEqual(payload["survey"]["id"], survey_id)

        # Consent
        resp = self.client.post(
            reverse("api_survey_participation", args=[survey_id]),
            data=json.dumps({"action": "consent"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # Submit
        resp = self.client.post(
            reverse("api_survey_responses", args=[survey_id]),
            data=json.dumps({"answers": {str(question_id): 4}}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        summary = self._json(resp)["scoreSummary"]
        self.assertEqual(summary["totalScore"], 4)
        participant = CustomUserSurveyParticipant.objects.get(survey_id=survey_id, user=self.student)
        self.assertEqual(participant.status, "completed")
        self.assertTrue(CustomUserSurveyResponse.objects.filter(participant=participant).exists())

        # Analytics for admin
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("api_survey_analytics", args=[survey_id]))
        self.assertEqual(resp.status_code, 200)
        analytics = self._json(resp)
        self.assertEqual(analytics["responseCount"], 1)
        self.assertTrue(analytics["charts"])


class GameQuestionManageTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username="builder",
            email="builder@example.com",
            password="pass",
            is_staff=True,
        )
        self.client.force_login(self.admin)
        self.game = Game.objects.create(
            title="Sample Quiz",
            description="",
            category="stem",
            difficulty="easy",
            duration_minutes=10,
            max_points=10,
            is_active=True,
            created_by=self.admin,
        )
        self.question = GameQuestion.objects.create(
            game=self.game,
            order=1,
            qtype="multiple-choice",
            question="2 + 2 = ?",
            options=["3", "4", "5"],
            correct_answer=1,
        )

    def test_manage_list_includes_answers(self):
        resp = self.client.get(reverse("api_game_questions_manage", args=[self.game.id]))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("questions", data)
        self.assertEqual(len(data["questions"]), 1)
        item = data["questions"][0]
        self.assertEqual(item["questionId"], self.question.id)
        self.assertEqual(item["correctAnswer"], 1)
        self.assertEqual(item["options"], ["3", "4", "5"])

    def test_update_question(self):
        payload = {
            "question": "Updated question?",
            "qtype": "multiple-choice",
            "options": ["Option A", "Option B", "Option C"],
            "correct_answer": 2,
            "order": 2,
        }
        resp = self.client.patch(
            reverse("api_game_question_manage", args=[self.game.id, self.question.id]),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.question.refresh_from_db()
        self.assertEqual(self.question.question, "Updated question?")
        self.assertEqual(self.question.correct_answer, 2)
        self.assertEqual(self.question.order, 2)

    def test_delete_question(self):
        resp = self.client.delete(
            reverse("api_game_question_manage", args=[self.game.id, self.question.id])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(GameQuestion.objects.filter(pk=self.question.id).exists())


class AuthPasswordResetTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="pass123",
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_forgot_password_sends_email_with_reset_link(self):
        payload = {"identifier": self.user.email}
        resp = self.client.post(
            reverse("api_forgot_password"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(self.user.email, email.to)
        self.assertIn("/reset-password/", email.body)
        self.assertIn("reset your", email.subject.lower())
