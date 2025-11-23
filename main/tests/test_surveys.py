import json

from django.test import TestCase
from django.urls import reverse

from main.models import CustomUser, CustomUserSurvey, CustomUserSurveyQuestion, CustomUserSurveyParticipant


class SurveyFieldlessQuestionTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="pass123",
        )
        self.survey = CustomUserSurvey.objects.create(
            title="Index Survey",
            is_active=True,
        )

    def test_required_choice_with_no_options_is_skipped(self):
        # Create a required single-choice question but without options (fieldless)
        CustomUserSurveyQuestion.objects.create(
            survey=self.survey,
            order=1,
            qtype="single-choice",
            prompt="Broken question",
            is_required=True,
            config={"options": []},
        )

        self.client.force_login(self.user)

        resp = self.client.post(
            reverse("api_survey_responses", args=[self.survey.id]),
            data=json.dumps({"answers": {}}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn("scoreSummary", payload)

        participant = CustomUserSurveyParticipant.objects.get(survey=self.survey, user=self.user)
        self.assertEqual(participant.status, "completed")
