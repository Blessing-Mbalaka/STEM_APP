from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from main.models.chatbot_config import ChatbotAnswerCache
from main.views.chatbotview import (
    OLLAMA_UNAVAILABLE_MESSAGE,
    _call_ollama_model,
    cache_response,
    call_primary_model,
    check_cache,
    get_chatbot_config,
)


class ChatbotProviderSelectionTests(SimpleTestCase):
    def setUp(self):
        self.ollama_config = SimpleNamespace(
            mode="ollama",
            ollama_api_base_url="http://localhost:11434",
            ollama_model="ministral-3:3b",
        )

    @patch("main.views.chatbotview.ChatbotConfig.load")
    def test_runtime_configuration_is_loaded(self, load_config):
        load_config.return_value = self.ollama_config

        self.assertIs(get_chatbot_config(), self.ollama_config)
        load_config.assert_called_once_with()

    @patch("main.views.chatbotview.requests.post")
    def test_ollama_allows_slow_vps_generation(self, post):
        post.return_value.json.return_value = {"response": "local answer"}

        response = _call_ollama_model("hello", self.ollama_config)

        self.assertEqual(response, "local answer")
        post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "ministral-3:3b",
                "prompt": "hello",
                "stream": False,
            },
            timeout=(5, 120),
        )

    @patch("main.views.chatbotview._call_gemini_model")
    @patch("main.views.chatbotview._call_ollama_model", return_value="local answer")
    def test_ollama_mode_uses_only_ollama(self, ollama_call, gemini_call):
        response = call_primary_model("hello", config=self.ollama_config)

        self.assertEqual(response, "local answer")
        ollama_call.assert_called_once()
        gemini_call.assert_not_called()

    @patch("main.views.chatbotview._call_gemini_model")
    @patch(
        "main.views.chatbotview._call_ollama_model",
        side_effect=TimeoutError("Ollama timed out"),
    )
    def test_ollama_failure_does_not_fall_back_to_gemini(
        self, ollama_call, gemini_call
    ):
        response = call_primary_model("hello", config=self.ollama_config)

        self.assertEqual(response, OLLAMA_UNAVAILABLE_MESSAGE)
        ollama_call.assert_called_once()
        gemini_call.assert_not_called()


class ChatbotAnswerCacheTests(TestCase):
    def setUp(self):
        self.config = SimpleNamespace(
            mode="ollama",
            ollama_api_base_url="http://localhost:11434",
            ollama_model="ministral-3:3b",
            allow_internet_search=True,
        )

    def test_exact_question_is_reused_across_case_and_spacing(self):
        cache_response(
            "  What is photosynthesis? ",
            "Plants convert light into chemical energy.",
            [{"title": "Biology notes"}],
            config=self.config,
        )

        result = check_cache("what   IS photosynthesis?", config=self.config)

        self.assertEqual(result["answer"], "Plants convert light into chemical energy.")
        self.assertEqual(result["sources"], [{"title": "Biology notes"}])
        self.assertEqual(ChatbotAnswerCache.objects.get().hit_count, 1)

    def test_provider_model_change_does_not_reuse_old_answer(self):
        cache_response("Explain gravity", "Cached answer", [], config=self.config)
        changed_config = SimpleNamespace(
            **{**vars(self.config), "ollama_model": "tinyllama:latest"}
        )

        self.assertIsNone(check_cache("Explain gravity", config=changed_config))

    def test_provider_errors_are_not_cached(self):
        cache_response(
            "Explain gravity",
            OLLAMA_UNAVAILABLE_MESSAGE,
            [],
            config=self.config,
        )

        self.assertFalse(ChatbotAnswerCache.objects.exists())
