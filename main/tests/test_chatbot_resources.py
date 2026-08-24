import json
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, TestCase

from main.models.course import Course, CourseResource
from main.utils.resources import build_resource_links, suggest_resource_links
from main.views.chatbotview import chatbot_api


class ChatbotResourceSuggestionTests(TestCase):
    def setUp(self):
        life_science = Course.objects.create(
            title="Life Science Grade 12",
            subject="Life Science",
            is_active=True,
        )
        mathematics = Course.objects.create(
            title="Mathematics Grade 12",
            subject="Mathematics",
            is_active=True,
        )
        physics = Course.objects.create(
            title="Physics Grade 12",
            subject="Physics",
            is_active=True,
        )
        self.dna = CourseResource.objects.create(
            course=life_science,
            title="Protein Synthesis and DNA",
            resource_type="youtube",
            url="https://example.com/dna",
        )
        CourseResource.objects.create(
            course=mathematics,
            title="Grade 12 Calculus",
            resource_type="video",
            url="https://example.com/calculus",
        )
        self.motion = CourseResource.objects.create(
            course=physics,
            title="Motion and Forces",
            resource_type="youtube",
            url="https://example.com/motion",
        )
        CourseResource.objects.create(
            course=life_science,
            title="Broken video",
            resource_type="youtube",
            url="https://example.com/watch/\ufffd",
        )

    def test_topic_title_is_ranked_first(self):
        suggestions = suggest_resource_links(
            "How does DNA protein synthesis work?", limit=3
        )

        self.assertEqual(suggestions[0]["resource_id"], str(self.dna.id))
        self.assertEqual(suggestions[0]["course"], "Life Science Grade 12")

    def test_topic_expansion_finds_related_video(self):
        suggestions = suggest_resource_links("Explain Newton's second law", limit=3)

        self.assertEqual(suggestions[0]["resource_id"], str(self.motion.id))

    def test_malformed_links_are_excluded(self):
        links = build_resource_links()

        self.assertNotIn("Broken video", {link["title"] for link in links})


class ChatbotSuggestionPayloadTests(SimpleTestCase):
    @patch("main.views.chatbotview.get_chatbot_config")
    @patch("main.views.chatbotview.suggest_resource_links")
    def test_chatbot_payload_includes_ranked_learning_links(
        self, suggest_links, get_config
    ):
        get_config.return_value = SimpleNamespace(is_enabled=True, mode="ollama")
        suggest_links.return_value = [
            {
                "title": "Algebra video",
                "course": "Mathematics",
                "resource_type": "video",
                "url": "https://example.com/algebra",
            }
        ]
        request = RequestFactory().post(
            "/api/chatbot/",
            data=json.dumps({"question": "2 + 2"}),
            content_type="application/json",
        )
        request.user = AnonymousUser()

        response = chatbot_api(request)
        payload = json.loads(response.content)

        self.assertEqual(payload["suggested_resources"], suggest_links.return_value)
