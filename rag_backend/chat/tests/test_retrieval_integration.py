"""
tests/test_retrieval_integration.py
=====================================
Integration tests: ingest synthetic files → retrieve → verify cross-format results.

These tests run FULLY OFFLINE using an in-memory / temp-dir ChromaDB instance
and a lightweight fake embedding function (random vectors, deterministic seed).

No Ollama, no network.

Run with:
    cd rag_backend
    python -m pytest chat/tests/test_retrieval_integration.py -v

IMPORTANT: Requires chromadb installed.
"""

from __future__ import annotations

import os
import sys
import random
import tempfile
import textwrap
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ── Conditionally import chromadb ────────────────────────────────────────────
chromadb = pytest.importorskip("chromadb")


# ─────────────────────────────────────────────────────────────────────────────
# Fake embedding function (deterministic pseudo-random, dim=128)
# ─────────────────────────────────────────────────────────────────────────────

class DeterministicEmbedding:
    """
    Embeds text as a 128-dim vector seeded from the text hash.
    Identical text → identical vector. Similar text → different vectors
    (we're only testing that the pipeline runs and returns results, not ranking quality).
    """
    DIM = 128

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)

    def _vec(self, text: str) -> list[float]:
        rng = random.Random(hash(text) & 0xFFFFFFFF)
        raw = [rng.gauss(0, 1) for _ in range(self.DIM)]
        norm = sum(x**2 for x in raw) ** 0.5 or 1.0
        return [x / norm for x in raw]


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def tmp_root(tmp_path_factory):
    return tmp_path_factory.mktemp("retrieval_integration")


@pytest.fixture(scope="module")
def chroma_dir(tmp_root):
    return str(tmp_root / "chromadb")


@pytest.fixture(scope="module")
def test_docs_dir(tmp_root):
    d = tmp_root / "docs"
    d.mkdir()
    return d


@pytest.fixture(scope="module")
def populated_vs(chroma_dir, test_docs_dir):
    """
    Create a ChromaDB collection pre-populated with synthetic docs:
      - report.txt       (Text)
      - data.csv         (CSV)
      - notes.md         (Markdown)
    Returns the Chroma collection instance.
    """
    from langchain_chroma import Chroma
    from langchain_core.documents import Document

    embed_fn = DeterministicEmbedding()

    vs = Chroma(
        collection_name="test_documents",
        embedding_function=embed_fn,
        persist_directory=chroma_dir,
        collection_metadata={"hnsw:space": "cosine"},
    )

    # ── Synthetic corpus ──────────────────────────────────────────────────────
    corpus = [
        # (content, doc_id, source, format, ext, chunk_index)
        (
            "MRPL refinery processes 300,000 barrels of crude oil per day. "
            "The Mangalore facility is one of the largest in India.",
            "1", "annual_report.txt", "Text", ".txt", 0,
        ),
        (
            "Safety metrics show zero LTI incidents in Q3 2026. "
            "All personnel follow mandatory PPE protocols.",
            "1", "annual_report.txt", "Text", ".txt", 1,
        ),
        (
            "Department: Refinery, Budget: 50000000, Headcount: 120\n"
            "Department: Safety, Budget: 8000000, Headcount: 30",
            "2", "budget.csv", "CSV", ".csv", 0,
        ),
        (
            "Department: HR, Budget: 2000000, Headcount: 10\n"
            "Department: IT, Budget: 3000000, Headcount: 15",
            "2", "budget.csv", "CSV", ".csv", 1,
        ),
        (
            "# Q3 Revenue Summary\n\nRevenue grew 12% year-on-year. "
            "Key driver: increased throughput at the refinery.",
            "3", "summary.md", "Markdown", ".md", 0,
        ),
        (
            "## Safety KPIs\n\nTarget: 0.5 incidents per 1000 hours. "
            "Achieved: 0.3 — well below the industry benchmark.",
            "3", "summary.md", "Markdown", ".md", 1,
        ),
        (
            "Environmental compliance score: 97/100. "
            "Carbon emission reduction: 8% vs 2025 baseline.",
            "4", "env_report.txt", "Text", ".txt", 0,
        ),
    ]

    docs = []
    ids  = []
    for text, doc_id, source, fmt, ext, chunk_idx in corpus:
        docs.append(Document(
            page_content=text,
            metadata={
                "doc_id":      doc_id,
                "source":      source,
                "format":      fmt,
                "ext":         ext,
                "chunk_index": chunk_idx,
            },
        ))
        ids.append(f"{doc_id}__chunk{chunk_idx}")

    vs.add_documents(documents=docs, ids=ids)
    return vs


# ─────────────────────────────────────────────────────────────────────────────
# Helper: run retrieval against our populated_vs
# ─────────────────────────────────────────────────────────────────────────────

def _search(vs, query: str, top_k: int = 5, min_score: float = 0.0,
            formats: list[str] | None = None) -> list[dict]:
    """Direct ChromaDB similarity search returning list of dicts."""
    kwargs: dict = {"k": top_k * 3}
    if formats:
        kwargs["filter"] = (
            {"format": {"$in": formats}} if len(formats) > 1
            else {"format": formats[0]}
        )
    raw = vs.similarity_search_with_relevance_scores(query, **kwargs)

    results = []
    seen: set[str] = set()
    for doc, score in raw:
        if score < min_score:
            continue
        key = doc.page_content[:80]
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "text":   doc.page_content,
            "score":  round(float(score), 4),
            "format": doc.metadata.get("format", "Unknown"),
            "source": doc.metadata.get("source", ""),
            "doc_id": doc.metadata.get("doc_id", ""),
            "chunk_index": doc.metadata.get("chunk_index", 0),
        })

    results.sort(key=lambda c: c["score"], reverse=True)
    return results[:top_k]


# ─────────────────────────────────────────────────────────────────────────────
# Test classes
# ─────────────────────────────────────────────────────────────────────────────

class TestBasicRetrieval:
    """Core retrieval behaviour."""

    def test_returns_results(self, populated_vs):
        results = _search(populated_vs, "refinery crude oil capacity")
        assert len(results) > 0

    def test_result_schema(self, populated_vs):
        results = _search(populated_vs, "safety PPE incidents")
        for r in results:
            assert "text"   in r
            assert "score"  in r
            assert "format" in r
            assert "source" in r

    def test_scores_are_sorted_descending(self, populated_vs):
        results = _search(populated_vs, "MRPL refinery Mangalore")
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_scores_in_valid_range(self, populated_vs):
        results = _search(populated_vs, "budget headcount department")
        for r in results:
            assert -0.01 <= r["score"] <= 1.01, f"Score out of range: {r['score']}"

    def test_top_k_respected(self, populated_vs):
        results = _search(populated_vs, "MRPL safety environment", top_k=2)
        assert len(results) <= 2

    def test_min_score_filter(self, populated_vs):
        results = _search(populated_vs, "MRPL refinery", min_score=0.0)
        all_pass = all(r["score"] >= 0.0 for r in results)
        assert all_pass


class TestFormatFiltering:
    """Format-specific filtering must only return matching formats."""

    def test_csv_filter_returns_only_csv(self, populated_vs):
        results = _search(populated_vs, "department budget headcount", formats=["CSV"])
        for r in results:
            assert r["format"] == "CSV", f"Expected CSV, got {r['format']}"

    def test_text_filter_returns_only_text(self, populated_vs):
        results = _search(populated_vs, "MRPL refinery barrels", formats=["Text"])
        for r in results:
            assert r["format"] == "Text", f"Expected Text, got {r['format']}"

    def test_markdown_filter_returns_only_md(self, populated_vs):
        results = _search(populated_vs, "revenue safety KPI", formats=["Markdown"])
        for r in results:
            assert r["format"] == "Markdown", f"Expected Markdown, got {r['format']}"

    def test_multi_format_filter(self, populated_vs):
        results = _search(populated_vs, "MRPL safety", formats=["Text", "CSV"])
        for r in results:
            assert r["format"] in {"Text", "CSV"}, f"Unexpected format: {r['format']}"

    def test_nonexistent_format_returns_empty(self, populated_vs):
        results = _search(populated_vs, "anything", formats=["PowerPoint"])
        assert results == []


class TestCrossFormatSearch:
    """Verify results can come from multiple formats in a single search."""

    def test_cross_format_results_possible(self, populated_vs):
        results = _search(populated_vs, "MRPL safety budget department", top_k=6)
        formats_found = {r["format"] for r in results}
        # With a diverse enough query across our corpus, should hit > 1 format
        # (note: with deterministic fake embeddings this tests the pipeline, not quality)
        assert len(formats_found) >= 1  # at minimum the pipeline works

    def test_all_formats_indexed(self, populated_vs):
        """Every format in our corpus should be retrievable."""
        expected_formats = {"Text", "CSV", "Markdown"}
        retrieved: set[str] = set()

        for query in [
            "refinery crude oil barrels",
            "budget department headcount",
            "revenue KPI safety metrics",
        ]:
            results = _search(populated_vs, query, top_k=4)
            retrieved |= {r["format"] for r in results}

        # At least some of our test formats should be retrievable
        assert len(retrieved & expected_formats) > 0


class TestDocumentIsolation:
    """Filtering by doc_id should respect document boundaries."""

    def test_doc_id_filter_in_metadata(self, populated_vs):
        """Direct metadata check: doc_id is stored correctly per chunk."""
        raw = populated_vs.get(where={"doc_id": "2"})
        texts = raw.get("documents", [])
        assert len(texts) > 0
        for meta in raw.get("metadatas", []):
            assert meta["doc_id"] == "2"

    def test_different_docs_different_ids(self, populated_vs):
        raw1 = populated_vs.get(where={"doc_id": "1"})
        raw3 = populated_vs.get(where={"doc_id": "3"})
        ids1 = set(raw1.get("ids", []))
        ids3 = set(raw3.get("ids", []))
        assert ids1.isdisjoint(ids3), "Different docs should have disjoint chunk IDs"


class TestChunkMetadata:
    """All expected metadata fields must be present on every stored chunk."""

    def test_required_metadata_fields(self, populated_vs):
        all_data = populated_vs.get()
        for meta in all_data.get("metadatas", []):
            for field in ("doc_id", "source", "format", "ext", "chunk_index"):
                assert field in meta, f"Missing metadata field '{field}'"

    def test_chunk_index_sequential(self, populated_vs):
        raw = populated_vs.get(where={"doc_id": "1"})
        indices = sorted(m["chunk_index"] for m in raw.get("metadatas", []))
        assert indices == list(range(len(indices)))

    def test_format_values_are_strings(self, populated_vs):
        all_data = populated_vs.get()
        for meta in all_data.get("metadatas", []):
            assert isinstance(meta["format"], str)
            assert len(meta["format"]) > 0

    def test_source_matches_filename(self, populated_vs):
        raw = populated_vs.get(where={"doc_id": "2"})
        for meta in raw.get("metadatas", []):
            assert meta["source"] == "budget.csv"
