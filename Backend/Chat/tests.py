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
            "citations": [{"index": 1, "source": "report.pdf", "chunk": 0, "score": 0.9, "snippet": "..."}],
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
        self.assertEqual(response.data.get("citations")[0]["index"], 1)
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
        self.assertEqual(result["citations"], [])

    @patch("chat.graph.retrieve_chunks", return_value=[])
    def test_no_relevant_chunks_returns_not_found(self, _mock_retrieve):
        result = ask_ollama("Something unrelated", thread_id="not-found-test")
        self.assertIn("couldn't find", result["answer"])
        self.assertEqual(result["sources"], [])
        self.assertEqual(result["citations"], [])

    @patch("chat.graph.get_llm")
    @patch("chat.graph.retrieve_chunks")
    def test_retrieved_chunks_reach_prompt_and_citations(self, mock_retrieve, mock_get_llm):
        mock_retrieve.return_value = [{
            "text": "The warranty lasts 2 years.",
            "source": "terms.pdf",
            "doc_id": "1",
            "chunk": 0,
            "score": 0.9,
        }]
        mock_get_llm.return_value.invoke.return_value = AIMessage("It lasts 2 years [1].")

        result = ask_ollama("How long is the warranty?", thread_id="generate-test")

        self.assertEqual(result["answer"], "It lasts 2 years [1].")
        self.assertEqual(result["sources"], ["terms.pdf"])
        self.assertEqual(result["citations"][0]["index"], 1)
        system_prompt = mock_get_llm.return_value.invoke.call_args[0][0][0].content
        self.assertIn("The warranty lasts 2 years.", system_prompt)
        self.assertIn("[1] (source: terms.pdf)", system_prompt)