from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from main.views.chatbotview import (
    OLLAMA_UNAVAILABLE_MESSAGE,
    call_primary_model,
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
