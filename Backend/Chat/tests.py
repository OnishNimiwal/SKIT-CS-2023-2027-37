from unittest.mock import patch

from django.urls import reverse
from langchain_core.messages import AIMessage
from rest_framework import status
from rest_framework.test import APITestCase

from .services import ask_ollama


class ChatAPITests(APITestCase):
    def setUp(self):
        self.chat_url = reverse("chat")

    @patch("chat.services.get_graph")
    def test_valid_message_success(self, mock_get_graph):
        mock_get_graph.return_value.invoke.return_value = {
            "messages": [AIMessage("Hello! I am your local AI assistant running on PC5.")],
            "sources": ["report.pdf"],
        }
        response = self.client.post(
            self.chat_url, {"message": "Hello AI", "thread_id": "t1"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("success"))
        self.assertEqual(
            response.data.get("response"),
            "Hello! I am your local AI assistant running on PC5.",
        )
        self.assertEqual(response.data.get("sources"), ["report.pdf"])
        self.assertEqual(response.data.get("model"), "local-ollama")
        self.assertFalse(response.data.get("external_api"))
        self.assertEqual(response.data.get("thread_id"), "t1")

    def test_empty_message(self):
        response = self.client.post(self.chat_url, {"message": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)

    def test_missing_message_field(self):
        response = self.client.post(self.chat_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)

    @patch("chat.services.get_graph")
    def test_graph_failure_returns_503(self, mock_get_graph):
        mock_get_graph.return_value.invoke.side_effect = Exception("Connection refused")
        response = self.client.post(
            self.chat_url, {"message": "Test server down"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(response.data.get("success"))
        self.assertEqual(response.data.get("error"), "Local AI server is unavailable.")

    @patch("chat.services.get_graph")
    def test_ask_ollama_service_direct(self, mock_get_graph):
        mock_get_graph.return_value.invoke.return_value = {
            "messages": [AIMessage("Direct service output")],
            "sources": [],
        }
        result = ask_ollama("Direct query")
        self.assertEqual(result["answer"], "Direct service output")
        self.assertEqual(result["sources"], [])

    @patch("chat.graph.retrieve", return_value=[])
    def test_no_relevant_chunks_returns_not_found(self, _mock_retrieve):
        result = ask_ollama("Something unrelated", thread_id="not-found-test")
        self.assertIn("couldn't find", result["answer"])
        self.assertEqual(result["sources"], [])