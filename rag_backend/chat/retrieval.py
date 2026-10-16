"""Document retrieval: find the chunks most relevant to a question."""

import re
from typing import TypedDict

from django.conf import settings

from .rag import get_vectorstore


class Chunk(TypedDict):
    text: str
    source: str
    doc_id: str
    chunk: int
    score: float


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def retrieve_chunks(
    query: str,
    doc_ids: list[str] | None = None,
    top_k: int | None = None,
    min_score: float | None = None,
    fetch_k: int | None = None,
) -> list[Chunk]:
    """
    Return the best chunks for a query, highest score first.

    1. Pull `fetch_k` candidates from the vector store (optionally limited to doc_ids).
    2. Drop chunks below `min_score`.
    3. Drop duplicate passages (same text after whitespace/case normalisation).
    4. Keep at most `top_k`.
    """
    query = (query or "").strip()
    if not query:
        return []

    top_k = top_k if top_k is not None else getattr(settings, "RAG_TOP_K", 4)
    min_score = min_score if min_score is not None else getattr(settings, "RAG_MIN_SCORE", 0.3)
    fetch_k = fetch_k if fetch_k is not None else getattr(settings, "RAG_FETCH_K", 12)
    fetch_k = max(fetch_k, top_k)

    flt = {"doc_id": {"$in": [str(d) for d in doc_ids]}} if doc_ids else None
    results = get_vectorstore().similarity_search_with_relevance_scores(
        query, k=fetch_k, filter=flt
    )

    chunks: list[Chunk] = []
    seen: set[str] = set()
    for doc, score in sorted(results, key=lambda r: r[1], reverse=True):
        if score < min_score:
            continue
        key = _normalize(doc.page_content)
        if not key or key in seen:
            continue
        seen.add(key)
        chunks.append({
            "text": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "doc_id": str(doc.metadata.get("doc_id", "")),
            "chunk": int(doc.metadata.get("chunk", 0)),
            "score": round(float(score), 4),
        })
        if len(chunks) >= top_k:
            break
    return chunks