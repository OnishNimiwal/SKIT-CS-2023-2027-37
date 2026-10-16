from unittest.mock import patch

from django.test import SimpleTestCase
from langchain_core.documents import Document

from .retrieval import retrieve_chunks


def _doc(text, source="a.pdf", doc_id="1", chunk=0):
    return Document(
        page_content=text,
        metadata={"source": source, "doc_id": doc_id, "chunk": chunk},
    )


@patch("chat.retrieval.get_vectorstore")
class RetrieveChunksTests(SimpleTestCase):
    def test_filters_low_scores(self, mock_store):
        mock_store.return_value.similarity_search_with_relevance_scores.return_value = [
            (_doc("good text"), 0.8),
            (_doc("weak text", chunk=1), 0.1),
        ]
        out = retrieve_chunks("q", top_k=4, min_score=0.3, fetch_k=8)
        self.assertEqual([c["text"] for c in out], ["good text"])

    def test_removes_duplicate_passages(self, mock_store):
        mock_store.return_value.similarity_search_with_relevance_scores.return_value = [
            (_doc("Same   text here"), 0.9),
            (_doc("same text HERE", chunk=1), 0.8),
        ]
        out = retrieve_chunks("q", top_k=4, min_score=0.3, fetch_k=8)
        self.assertEqual(len(out), 1)

    def test_sorts_by_score_and_caps_top_k(self, mock_store):
        mock_store.return_value.similarity_search_with_relevance_scores.return_value = [
            (_doc("low", chunk=0), 0.5),
            (_doc("high", chunk=1), 0.9),
            (_doc("mid", chunk=2), 0.7),
        ]
        out = retrieve_chunks("q", top_k=2, min_score=0.3, fetch_k=8)
        self.assertEqual([c["text"] for c in out], ["high", "mid"])

    def test_passes_document_filter(self, mock_store):
        store = mock_store.return_value.similarity_search_with_relevance_scores
        store.return_value = []
        retrieve_chunks("q", doc_ids=["1", 2], top_k=4, min_score=0.3, fetch_k=8)
        self.assertEqual(store.call_args.kwargs["filter"], {"doc_id": {"$in": ["1", "2"]}})

    def test_empty_query_skips_search(self, mock_store):
        self.assertEqual(retrieve_chunks("   "), [])
        mock_store.return_value.similarity_search_with_relevance_scores.assert_not_called()

    def test_chunk_fields(self, mock_store):
        mock_store.return_value.similarity_search_with_relevance_scores.return_value = [
            (_doc("text", source="r.pdf", doc_id="7", chunk=3), 0.91234),
        ]
        out = retrieve_chunks("q", top_k=4, min_score=0.3, fetch_k=8)
        self.assertEqual(
            out[0],
            {"text": "text", "source": "r.pdf", "doc_id": "7", "chunk": 3, "score": 0.9123},
        )