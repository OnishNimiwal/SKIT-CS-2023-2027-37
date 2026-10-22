"""Document retrieval: find the chunks most relevant to a question.

Cross-format aware — results may come from PDFs, spreadsheets,
presentations, images, or audio transcripts.
"""

from __future__ import annotations

import re
from typing import TypedDict

from django.conf import settings

from .rag import get_vectorstore


class Chunk(TypedDict):
    text: str
    source: str
    doc_id: str
    chunk_index: int
    format: str       # "PDF", "Excel Spreadsheet", "Image (OCR)", etc.
    score: float


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def retrieve_chunks(
    query: str,
    doc_ids: list[str] | None = None,
    formats: list[str] | None = None,
    top_k: int | None = None,
    min_score: float | None = None,
    fetch_k: int | None = None,
) -> list[Chunk]:
    """
    Return the best chunks for a query, highest score first.

    Steps:
      1. Pull `fetch_k` candidates from the vector store.
         Optionally filter by doc_ids and/or formats.
      2. Drop chunks below `min_score`.
      3. Deduplicate identical passages.
      4. Return top `top_k` results.

    Args:
        query:    Natural-language question or keywords.
        doc_ids:  Optional list of doc IDs to restrict search to.
        formats:  Optional list of format labels ("PDF", "CSV", etc.) to restrict to.
        top_k:    Maximum results to return. Defaults to RAG_TOP_K setting.
        min_score: Minimum cosine-similarity score (0–1). Defaults to RAG_MIN_SCORE.
        fetch_k:   Candidates to fetch before filtering. Defaults to 4× top_k.

    Returns:
        List of Chunk TypedDicts sorted by descending relevance score.
    """
    query = (query or "").strip()
    if not query:
        return []

    cfg_top_k    = getattr(settings, "RAG_TOP_K", 6)
    cfg_min_score = getattr(settings, "RAG_MIN_SCORE", 0.20)
    cfg_fetch_k  = getattr(settings, "RAG_FETCH_K", cfg_top_k * 4)

    top_k    = top_k    if top_k    is not None else cfg_top_k
    min_score = min_score if min_score is not None else cfg_min_score
    fetch_k  = fetch_k  if fetch_k  is not None else cfg_fetch_k

    vs = get_vectorstore()

    # ── Build optional ChromaDB where-filter ─────────────────────────────────
    where: dict | None = None
    conditions: list[dict] = []

    if doc_ids:
        str_ids = [str(d) for d in doc_ids]
        conditions.append(
            {"doc_id": {"$in": str_ids}}
            if len(str_ids) > 1 else
            {"doc_id": str_ids[0]}
        )

    if formats:
        conditions.append(
            {"format": {"$in": formats}}
            if len(formats) > 1 else
            {"format": formats[0]}
        )

    if len(conditions) == 1:
        where = conditions[0]
    elif len(conditions) > 1:
        where = {"$and": conditions}

    # ── Similarity search with relevance scores ───────────────────────────────
    kwargs: dict = {"k": fetch_k}
    if where:
        kwargs["filter"] = where

    try:
        raw = vs.similarity_search_with_relevance_scores(query, **kwargs)
    except Exception:
        raw = []

    # ── Filter, deduplicate, rank ─────────────────────────────────────────────
    seen: set[str] = set()
    results: list[Chunk] = []

    for doc, score in raw:
        if score < min_score:
            continue
        key = _normalize(doc.page_content)
        if key in seen:
            continue
        seen.add(key)

        meta = doc.metadata
        results.append(
            Chunk(
                text=doc.page_content,
                source=meta.get("source", ""),
                doc_id=meta.get("doc_id", ""),
                chunk_index=meta.get("chunk_index", 0),
                format=meta.get("format", "Unknown"),
                score=round(float(score), 4),
            )
        )

    # sort highest score first
    results.sort(key=lambda c: c["score"], reverse=True)
    return results[:top_k]
