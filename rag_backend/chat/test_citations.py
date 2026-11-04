from django.test import SimpleTestCase

from .citations import cited_indexes, select_citations

CITATIONS = [
    {"index": 1, "source": "a.pdf", "chunk": 0, "score": 0.9, "snippet": "A"},
    {"index": 2, "source": "b.pdf", "chunk": 1, "score": 0.8, "snippet": "B"},
    {"index": 3, "source": "c.pdf", "chunk": 2, "score": 0.7, "snippet": "C"},
]


class CitedIndexesTests(SimpleTestCase):
    def test_single_and_adjacent_markers(self):
        self.assertEqual(cited_indexes("One [1] and two [3][2].", 3), [1, 2, 3])

    def test_comma_separated_marker(self):
        self.assertEqual(cited_indexes("Both [1, 2].", 3), [1, 2])

    def test_ignores_out_of_range(self):
        self.assertEqual(cited_indexes("Bad [0] and [9].", 3), [])

    def test_empty_answer(self):
        self.assertEqual(cited_indexes("", 3), [])
        self.assertEqual(cited_indexes(None, 3), [])


class SelectCitationsTests(SimpleTestCase):
    def test_keeps_only_cited(self):
        out = select_citations("Only the second [2].", CITATIONS)
        self.assertEqual([c["index"] for c in out], [2])

    def test_returns_all_when_nothing_cited(self):
        self.assertEqual(select_citations("No markers here.", CITATIONS), CITATIONS)

    def test_handles_missing_answer(self):
        self.assertEqual(select_citations(None, CITATIONS), CITATIONS)