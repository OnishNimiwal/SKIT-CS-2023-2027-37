"""
retrieval.py
============
Document retrieval: surface the most relevant chunks for a query.

Cross-format aware — results may come from PDFs, spreadsheets,
presentations, images, or audio transcripts.

This module re-exports everything from semantic_search.py so callers
only need to import from one place.
"""

from __future__ import annotations

import re
from typing import TypedDict

from django.conf import settings

from .rag import get_vectorstore
from .semantic_search import (
    SemanticChunk,
    semantic_search,
    group_by_format,
    build_context_string,
    FORMAT_COLORS,
)

# ── Re-export public symbols ──────────────────────────────────────────────────
__all__ = [
    "retrieve_chunks",
    "retrieve_context",
    "SemanticChunk",
    "semantic_search",
    "group_by_format",
    "build_context_string",
    "FORMAT_COLORS",
]


class Chunk(TypedDict):
    """Legacy type kept for backward compatibility."""
    text: str
    source: str
    doc_id: str
    chunk_index: int
    format: str
    score: float


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


# ─────────────────────────────────────────────────────────────────────────────
# Primary API — enhanced semantic retrieval
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_chunks(
    query: str,
    doc_ids: list[str] | None = None,
    formats: list[str] | None = None,
    top_k: int | None = None,
    min_score: float | None = None,
    fetch_k: int | None = None,
    *,
    # Enhancement flags (can be overridden per-call)
    use_mmr: bool = True,
    use_bm25: bool = True,
    expand_context: bool = True,
) -> list[SemanticChunk]:
    """
    Retrieve semantically relevant chunks from ChromaDB.

    Uses:
      • OllamaEmbeddings (nomic-embed-text) for vector similarity
      • BM25 keyword re-scoring for precise term matching
      • MMR for result diversity
      • Adjacent-chunk context expansion

    Args:
        query:          Natural-language question or keywords.
        doc_ids:        Restrict to specific document IDs (optional).
        formats:        Restrict to specific format labels (optional).
        top_k:          Max results to return (default: settings.RAG_TOP_K).
        min_score:      Minimum vector similarity to include (default: settings.RAG_MIN_SCORE).
        fetch_k:        Candidates fetched before re-ranking.
        use_mmr:        Enable Maximal Marginal Relevance diversification.
        use_bm25:       Enable BM25 keyword boost in final scoring.
        expand_context: Merge adjacent chunks for richer context.

    Returns:
        List of SemanticChunk dicts sorted by final_score descending.
        Each chunk includes: text, context, source, doc_id, chunk_index,
        format, format_color, vector_score, bm25_score, final_score.
    """
    return semantic_search(
        query=query,
        doc_ids=doc_ids,
        formats=formats,
        top_k=top_k,
        min_score=min_score,
        fetch_k=fetch_k,
        mmr_lambda=0.65 if use_mmr else 1.0,     # λ=1 → pure relevance (no MMR diversity)
        bm25_weight=0.25 if use_bm25 else 0.0,
        expand_context=expand_context,
        context_window=1,
    )


def retrieve_context(
    query: str,
    doc_ids: list[str] | None = None,
    formats: list[str] | None = None,
    top_k: int | None = None,
) -> str:
    """
    Convenience wrapper: retrieve relevant chunks and return a single
    formatted context string ready to inject into an LLM prompt.

    Returns:
        Multi-block text string with headers:
        "[Source N: filename | format | score=X]\nchunk text\n"
    """
    chunks = retrieve_chunks(
        query=query,
        doc_ids=doc_ids,
        formats=formats,
        top_k=top_k,
    )
    return build_context_string(chunks)
