from django.test import SimpleTestCase
from langchain_core.messages import AIMessage, HumanMessage

from .prompts import (
    build_condense_prompt,
    build_rewrite_prompt,
    build_system_prompt,
    format_context,
)

CHUNKS = [
    {"text": "First passage.", "source": "a.pdf", "doc_id": "1", "chunk": 0, "score": 0.9},
    {"text": "Second passage.", "source": "b.docx", "doc_id": "2", "chunk": 4, "score": 0.8},
]


class PromptTests(SimpleTestCase):
    def test_context_is_numbered_with_sources(self):
        text = format_context(CHUNKS)
        self.assertIn("[1] (source: a.pdf)\nFirst passage.", text)
        self.assertIn("[2] (source: b.docx)\nSecond passage.", text)

    def test_system_prompt_has_rules_and_context(self):
        prompt = build_system_prompt(CHUNKS)
        self.assertIn("ONLY the numbered context passages", prompt)
        self.assertIn("Cite the passages", prompt)
        self.assertIn("First passage.", prompt)

    def test_braces_in_documents_do_not_break_prompt(self):
        chunks = [{"text": "config = {a: 1}", "source": "c.md", "doc_id": "3", "chunk": 0, "score": 0.9}]
        self.assertIn("config = {a: 1}", build_system_prompt(chunks))

    def test_condense_prompt_includes_history_and_question(self):
        history = [HumanMessage("What is the policy?"), AIMessage("It covers 2 years.")]
        prompt = build_condense_prompt(history, "and the price?")
        self.assertIn("User: What is the policy?", prompt)
        self.assertIn("Assistant: It covers 2 years.", prompt)
        self.assertIn("Follow-up: and the price?", prompt)

    def test_rewrite_prompt_includes_question_and_asks_for_keywords(self):
        prompt = build_rewrite_prompt("how long is the warranty {x}?")
        self.assertIn("how long is the warranty {x}?", prompt)
        self.assertIn("keyword-style search query", prompt)