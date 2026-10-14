from unittest.mock import patch, Mock
import requests
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from django.test import override_settings
from rest_framework.test import APITestCase
from .services import ask_ollama, ollama_options

class ChatAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='test-pass-123')
        self.client.force_login(self.user)
        self.chat_url = reverse("chat")

    @patch("chat.services.requests.post")
    def test_valid_message_success(self, mock_post):
        """Test sending a valid message returns successful AI response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "qwen3:4b",
            "response": "Hello! I am your local AI assistant running on PC5.",
            "done": True,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        response = self.client.post(
            self.chat_url,
            {"message": "Hello AI"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("success"))
        self.assertEqual(
            response.data.get("response"),
            "Hello! I am your local AI assistant running on PC5."
        )
        self.assertEqual(response.data.get("model"), "local-ollama")
        self.assertFalse(response.data.get("external_api"))

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["prompt"], "Hello AI")
        self.assertFalse(kwargs["json"]["stream"])

    def test_empty_message(self):
        """Test that an empty message string returns 400 Bad Request."""
        response = self.client.post(
            self.chat_url,
            {"message": ""},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)

    def test_missing_message_field(self):
        """Test that omitting the message field returns 400 Bad Request."""
        response = self.client.post(
            self.chat_url,
            {},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)

    @patch("chat.services.requests.post")
    def test_ollama_server_connection_error(self, mock_post):
        """Test that connection failure to Ollama returns HTTP 503."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        response = self.client.post(
            self.chat_url,
            {"message": "Test server down"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(response.data.get("success"))
        self.assertEqual(
            response.data.get("error"),
            "Local AI server is unavailable."
        )

    @patch("chat.services.requests.post")
    def test_ollama_server_timeout(self, mock_post):
        """Test that timeout when contacting Ollama returns HTTP 503."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        response = self.client.post(
            self.chat_url,
            {"message": "Test timeout"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(response.data.get("success"))
        self.assertEqual(
            response.data.get("error"),
            "Local AI server is unavailable."
        )

    @patch("chat.services.requests.post")
    def test_ollama_server_http_error(self, mock_post):
        """Test that HTTP error (e.g. 500) from Ollama returns HTTP 503."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        response = self.client.post(
            self.chat_url,
            {"message": "Test HTTP error"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(response.data.get("success"))
        self.assertEqual(
            response.data.get("error"),
            "Local AI server is unavailable."
        )

    @patch("chat.services.requests.post")
    def test_ask_ollama_service_direct(self, mock_post):
        """Direct unit test for ask_ollama service function."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Direct service output"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = ask_ollama("Direct query")
        self.assertEqual(result, "Direct service output")


class OllamaOptionsTests(APITestCase):
    """Speed options added to every Ollama request (think flag, keep_alive)."""

    @override_settings(OLLAMA_THINK=False, OLLAMA_KEEP_ALIVE="30m", OLLAMA_THINKING_MODELS=["qwen3"])
    def test_thinking_model_gets_think_false_and_keep_alive(self):
        self.assertEqual(ollama_options("qwen3:8b"), {"keep_alive": "30m", "think": False})

    @override_settings(OLLAMA_THINK=False, OLLAMA_KEEP_ALIVE="30m", OLLAMA_THINKING_MODELS=["qwen3"])
    def test_non_thinking_model_gets_no_think_flag(self):
        self.assertEqual(ollama_options("llama3.2:3b"), {"keep_alive": "30m"})

    @override_settings(OLLAMA_THINK=None, OLLAMA_KEEP_ALIVE="", OLLAMA_THINKING_MODELS=["qwen3"])
    def test_model_default_sends_nothing(self):
        self.assertEqual(ollama_options("qwen3:8b"), {})

    @override_settings(OLLAMA_MODEL="qwen3:8b", OLLAMA_THINK=False, OLLAMA_KEEP_ALIVE="30m",
                       OLLAMA_THINKING_MODELS=["qwen3"])
    @patch("chat.services.requests.post")
    def test_ask_ollama_sends_speed_options(self, mock_post):
        mock_post.return_value = Mock(json=Mock(return_value={"response": "Paris"}), raise_for_status=Mock())
        self.assertEqual(ask_ollama("Capital of France?"), "Paris")
        payload = mock_post.call_args.kwargs["json"]
        self.assertIs(payload["think"], False)
        self.assertEqual(payload["keep_alive"], "30m")
