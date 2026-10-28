from django.test import SimpleTestCase

from .guards import classify_question, smalltalk_reply, validate_question


class ValidateQuestionTests(SimpleTestCase):
    def test_accepts_normal_question(self):
        self.assertEqual(validate_question("What is the policy?", max_chars=100), (True, ""))

    def test_rejects_empty_question(self):
        ok, message = validate_question("   ", max_chars=100)
        self.assertFalse(ok)
        self.assertIn("enter a question", message)

    def test_rejects_too_long_question(self):
        ok, message = validate_question("x" * 11, max_chars=10)
        self.assertFalse(ok)
        self.assertIn("too long", message)


class ClassifyQuestionTests(SimpleTestCase):
    def test_small_talk_is_detected(self):
        for text in ["hello", "Hi!!", "Thank you!", "bye", "What can you do?", "Good morning"]:
            self.assertEqual(classify_question(text), "smalltalk", text)

    def test_document_questions_go_to_rag(self):
        for text in [
            "What is the warranty period?",
            "Hello, what is the warranty period?",
            "help me find the refund policy",
        ]:
            self.assertEqual(classify_question(text), "rag", text)

    def test_replies(self):
        self.assertIn("Upload", smalltalk_reply("hello"))
        self.assertIn("welcome", smalltalk_reply("thanks"))
        self.assertIn("Goodbye", smalltalk_reply("bye"))
        self.assertIn("cite", smalltalk_reply("what can you do"))