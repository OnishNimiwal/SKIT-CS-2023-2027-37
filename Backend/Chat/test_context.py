from django.test import SimpleTestCase
from langchain_core.messages import AIMessage, HumanMessage

from .context import fit_chunks_to_budget, trim_history


def _chunk(text, i=0):
    return {"text": text, "source": "a.pdf", "doc_id": "1", "chunk": i, "score": 0.9}


class FitChunksTests(SimpleTestCase):
    def test_keeps_everything_that_fits(self):
        chunks = [_chunk("a" * 100, 0), _chunk("b" * 100, 1)]
        self.assertEqual(fit_chunks_to_budget(chunks, max_chars=500), chunks)

    def test_drops_chunks_over_budget(self):
        chunks = [_chunk("a" * 400, 0), _chunk("b" * 400, 1)]
        out = fit_chunks_to_budget(chunks, max_chars=500)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["chunk"], 0)

    def test_truncates_when_enough_room_is_left(self):
        chunks = [_chunk("a" * 300, 0), _chunk("b" * 400, 1)]
        out = fit_chunks_to_budget(chunks, max_chars=600)
        self.assertEqual(len(out), 2)
        self.assertTrue(out[1]["text"].endswith("…"))
        self.assertLessEqual(len(out[1]["text"]), 300)

    def test_single_oversized_chunk_is_truncated_not_dropped(self):
        out = fit_chunks_to_budget([_chunk("a" * 1000)], max_chars=100)
        self.assertEqual(len(out), 1)
        self.assertLessEqual(len(out[0]["text"]), 100)

    def test_empty_input(self):
        self.assertEqual(fit_chunks_to_budget([], max_chars=100), [])


class TrimHistoryTests(SimpleTestCase):
    def setUp(self):
        self.msgs = [
            HumanMessage("a" * 10),
            AIMessage("b" * 10),
            HumanMessage("c" * 10),
            AIMessage("d" * 10),
            HumanMessage("e"),
        ]

    def test_limits_message_count(self):
        out = trim_history(self.msgs, max_messages=3, max_chars=1000)
        self.assertEqual([m.content[0] for m in out], ["c", "d", "e"])

    def test_limits_characters_by_dropping_oldest(self):
        out = trim_history(self.msgs, max_messages=10, max_chars=25)
        self.assertEqual([m.content[0] for m in out], ["c", "d", "e"])

    def test_starts_on_a_user_turn(self):
        out = trim_history(self.msgs, max_messages=2, max_chars=1000)
        self.assertEqual(out[0].type, "human")

    def test_always_keeps_latest_message(self):
        out = trim_history(self.msgs, max_messages=10, max_chars=0)
        self.assertEqual(out[-1].content, "e")

    def test_empty_history(self):
        self.assertEqual(trim_history([], max_messages=5, max_chars=100), [])