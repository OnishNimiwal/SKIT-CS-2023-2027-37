from unittest.mock import patch, Mock
import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .services import ask_ollama

class ChatAPITests(APITestCase):
    def setUp(self):
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
