"""
semantic_search.py
==================
Enhanced semantic similarity search for the MRPL AI Workbench.

Layers on top of the basic ChromaDB retrieval:
  1. Query pre-processing  — stopword stripping, keyword extraction
  2. Maximal Marginal Relevance (MMR) — diversity so you don't get
     10 chunks from the same paragraph
  3. Hybrid BM25 + vector re-scoring — boosts chunks that contain
     exact query keywords (handles acronyms / product codes well)
  4. Adjacent-chunk context expansion — merge neighbouring chunks so
     answers are never cut mid-sentence
  5. Cross-format result grouping  — surface which formats contributed

All of this is format-agnostic: results come from PDF, DOCX, XLSX,
CSV, PPTX, Images (OCR) and Audio transcripts alike.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter, defaultdict
from typing import TypedDict

from django.conf import settings

from .rag import get_vectorstore

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Type definitions
# ─────────────────────────────────────────────────────────────────────────────

class SemanticChunk(TypedDict):
    text: str
    source: str
    doc_id: str
    chunk_index: int
    format: str
    format_color: str
    vector_score: float    # raw cosine similarity (0–1)
    bm25_score: float      # TF-IDF keyword boost (0–1)
    final_score: float     # weighted combination
    context: str           # expanded text with adjacent chunks (may == text)


FORMAT_COLORS: dict[str, str] = {
    "PDF":               "#ef4444",
    "Word Document":     "#3b82f6",
    "Text":              "#64748b",
    "Markdown":          "#8b5cf6",
    "Excel Spreadsheet": "#22c55e",
    "CSV":               "#10b981",
    "TSV":               "#14b8a6",
    "PowerPoint":        "#f97316",
    "Image (OCR)":       "#f59e0b",
    "Audio Transcript":  "#6366f1",
    "Unknown":           "#94a3b8",
}

_STOPWORDS = frozenset(
    "a an the and or not is are was were be been being have has had do does "
    "did will would could should may might shall can i we you he she it they "
    "in on at to for of with by from up about into through during before after "
    "above below between what who how when where why which this that these those "
    "then than so but if as".split()
)


# ─────────────────────────────────────────────────────────────────────────────
# Query pre-processing
# ─────────────────────────────────────────────────────────────────────────────

def _tokenise(text: str) -> list[str]:
    return [
        t.lower() for t in re.findall(r"\b[a-zA-Z0-9_\-]+\b", text)
        if len(t) >= 2
    ]


def _extract_keywords(query: str) -> list[str]:
    """Return meaningful tokens from the query (stopwords removed)."""
    return [t for t in _tokenise(query) if t not in _STOPWORDS]


# ─────────────────────────────────────────────────────────────────────────────
# BM25-lite scorer
# ─────────────────────────────────────────────────────────────────────────────

def _bm25_score(
    query_terms: list[str],
    doc_text: str,
    avg_doc_len: float = 300.0,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """
    Approximate BM25 score for a single document against query terms.
    Normalised to [0, 1] by dividing by (k1+1)*len(query_terms).
    """
    tokens = _tokenise(doc_text)
    doc_len = len(tokens)
    tf_map = Counter(tokens)

    score = 0.0
    for term in query_terms:
        tf = tf_map.get(term, 0)
        numerator   = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * doc_len / max(avg_doc_len, 1))
        score += numerator / max(denominator, 1e-9)

    # normalise
    max_possible = (k1 + 1) * len(query_terms) if query_terms else 1
    return min(score / max_possible, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# MMR (Maximal Marginal Relevance)
# ─────────────────────────────────────────────────────────────────────────────

def _cosine_text(a: str, b: str) -> float:
    """Very lightweight text cosine similarity using TF bags."""
    va, vb = Counter(_tokenise(a)), Counter(_tokenise(b))
    keys = set(va) | set(vb)
    if not keys:
        return 0.0
    dot = sum(va.get(k, 0) * vb.get(k, 0) for k in keys)
    mag_a = math.sqrt(sum(v**2 for v in va.values()))
    mag_b = math.sqrt(sum(v**2 for v in vb.values()))
    return dot / max(mag_a * mag_b, 1e-9)


def _mmr_select(
    candidates: list[dict],      # [{text, final_score, ...}]
    top_k: int,
    lambda_: float = 0.6,        # 1.0 = pure relevance, 0.0 = pure diversity
) -> list[dict]:
    """
    Select `top_k` items using MMR to balance relevance and diversity.
    Uses lightweight text cosine for inter-document similarity.
    """
    selected: list[dict] = []
    remaining = list(candidates)

    while remaining and len(selected) < top_k:
        if not selected:
            # Pick the highest-scoring first
            best = max(remaining, key=lambda c: c["final_score"])
        else:
            # MMR score = λ·relevance − (1-λ)·max_sim_to_already_selected
            def mmr_score(c: dict) -> float:
                rel = c["final_score"]
                max_sim = max(
                    _cosine_text(c["text"], s["text"])
                    for s in selected
                )
                return lambda_ * rel - (1 - lambda_) * max_sim

            best = max(remaining, key=mmr_score)

        selected.append(best)
        remaining.remove(best)

    return selected


# ─────────────────────────────────────────────────────────────────────────────
# Context expansion (adjacent-chunk merger)
# ─────────────────────────────────────────────────────────────────────────────

def _expand_context(
    chunk: dict,
    all_raw: list,          # list of (Document, score) from ChromaDB
    window: int = 1,        # number of adjacent chunks to include each side
) -> str:
    """Merge the target chunk with its immediate neighbours for richer context."""
    target_idx   = chunk["chunk_index"]
    target_doc   = chunk["doc_id"]
    target_src   = chunk["source"]

    neighbours: dict[int, str] = {}
    for doc, _score in all_raw:
        m = doc.metadata
        if m.get("doc_id") == target_doc and m.get("source") == target_src:
            idx = m.get("chunk_index", -1)
            if abs(idx - target_idx) <= window:
                neighbours[idx] = doc.page_content

    ordered = [neighbours[i] for i in sorted(neighbours) if i in neighbours]
    return "\n".join(ordered) if ordered else chunk["text"]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def semantic_search(
    query: str,
    doc_ids: list[str] | None = None,
    formats: list[str] | None = None,
    top_k: int | None = None,
    min_score: float | None = None,
    fetch_k: int | None = None,
    mmr_lambda: float = 0.65,
    bm25_weight: float = 0.25,
    expand_context: bool = True,
    context_window: int = 1,
) -> list[SemanticChunk]:
    """
    Retrieve semantically relevant chunks from ChromaDB with enhanced ranking.

    Pipeline:
        1. Pull `fetch_k` candidates via vector similarity (OllamaEmbeddings)
        2. Apply format/doc_id metadata filter
        3. Score each candidate with BM25 for keyword precision
        4. Combine: final = (1-bm25_weight)·vector + bm25_weight·bm25
        5. Apply MMR to diversify results
        6. Optionally expand each chunk with adjacent neighbour context
        7. Return top `top_k` results enriched with format metadata

    Args:
        query:          Natural-language question or keywords.
        doc_ids:        Restrict search to these document IDs (optional).
        formats:        Restrict search to these format labels (optional).
        top_k:          Max results to return (default: RAG_TOP_K setting).
        min_score:      Minimum vector similarity to admit (default: RAG_MIN_SCORE).
        fetch_k:        Candidates fetched from ChromaDB before re-ranking.
        mmr_lambda:     MMR relevance weight (0=pure diversity, 1=pure relevance).
        bm25_weight:    Weight of BM25 keyword score in final ranking (0–1).
        expand_context: If True, merge adjacent chunks for richer context.
        context_window: Adjacent chunk radius for context expansion.

    Returns:
        List of SemanticChunk dicts sorted by final_score descending.
    """
    query = (query or "").strip()
    if not query:
        return []

    # ── Settings defaults ────────────────────────────────────────────────────
    cfg_top_k     = getattr(settings, "RAG_TOP_K",    6)
    cfg_min_score = getattr(settings, "RAG_MIN_SCORE", 0.20)
    cfg_fetch_k   = getattr(settings, "RAG_FETCH_K",   cfg_top_k * 4)

    top_k     = top_k     if top_k     is not None else cfg_top_k
    min_score = min_score if min_score is not None else cfg_min_score
    fetch_k   = max(fetch_k if fetch_k is not None else cfg_fetch_k, top_k * 4)

    keywords = _extract_keywords(query)

    # ── ChromaDB filter ──────────────────────────────────────────────────────
    conditions: list[dict] = []
    if doc_ids:
        str_ids = [str(d) for d in doc_ids]
        conditions.append(
            {"doc_id": {"$in": str_ids}} if len(str_ids) > 1
            else {"doc_id": str_ids[0]}
        )
    if formats:
        conditions.append(
            {"format": {"$in": formats}} if len(formats) > 1
            else {"format": formats[0]}
        )
    where = (
        {"$and": conditions} if len(conditions) > 1
        else conditions[0]   if len(conditions) == 1
        else None
    )

    # ── Vector similarity search ─────────────────────────────────────────────
    vs = get_vectorstore()
    kwargs: dict = {"k": fetch_k}
    if where:
        kwargs["filter"] = where

    try:
        raw = vs.similarity_search_with_relevance_scores(query, **kwargs)
    except Exception as exc:
        logger.error("ChromaDB search failed: %s", exc)
        return []

    if not raw:
        return []

    # ── Score candidates ─────────────────────────────────────────────────────
    seen_text: set[str] = set()
    candidates: list[dict] = []

    for doc, v_score in raw:
        if v_score < min_score:
            continue
        norm_key = re.sub(r"\s+", " ", doc.page_content).strip().lower()
        if norm_key in seen_text:
            continue
        seen_text.add(norm_key)

        b_score = _bm25_score(keywords, doc.page_content) if keywords else 0.0
        final   = (1 - bm25_weight) * v_score + bm25_weight * b_score

        meta = doc.metadata
        fmt  = meta.get("format", "Unknown")
        candidates.append({
            "text":        doc.page_content,
            "source":      meta.get("source", ""),
            "doc_id":      meta.get("doc_id", ""),
            "chunk_index": meta.get("chunk_index", 0),
            "format":      fmt,
            "format_color": FORMAT_COLORS.get(fmt, FORMAT_COLORS["Unknown"]),
            "vector_score": round(float(v_score), 4),
            "bm25_score":   round(float(b_score), 4),
            "final_score":  round(float(final), 4),
            "context":     doc.page_content,   # will be expanded below
        })

    if not candidates:
        return []

    # Sort by final score before MMR
    candidates.sort(key=lambda c: c["final_score"], reverse=True)

    # ── MMR diversification ───────────────────────────────────────────────────
    # Fetch more than top_k so MMR can diversify then trim
    diverse = _mmr_select(candidates, top_k=min(top_k * 2, len(candidates)), lambda_=mmr_lambda)

    # ── Context expansion ─────────────────────────────────────────────────────
    if expand_context:
        for c in diverse:
            c["context"] = _expand_context(c, raw, window=context_window)

    # Sort final selection and trim
    diverse.sort(key=lambda c: c["final_score"], reverse=True)
    result = diverse[:top_k]

    logger.info(
        "semantic_search: query=%r → %d/%d candidates → %d results (formats: %s)",
        query[:60], len(candidates), fetch_k, len(result),
        ", ".join(sorted({c["format"] for c in result})),
    )
    return result


def group_by_format(chunks: list[SemanticChunk]) -> dict[str, list[SemanticChunk]]:
    """Group result chunks by their source format for display."""
    groups: dict[str, list] = defaultdict(list)
    for c in chunks:
        groups[c["format"]].append(c)
    return dict(groups)


def build_context_string(
    chunks: list[SemanticChunk],
    max_chars: int | None = None,
    use_expanded: bool = True,
) -> str:
    """
    Build a plain-text context block to feed into an LLM prompt.
    Uses expanded context if available, truncates to max_chars.
    """
    limit = max_chars or getattr(settings, "RAG_MAX_CONTEXT_CHARS", 6000)
    parts: list[str] = []
    total = 0

    for i, c in enumerate(chunks, 1):
        body = c["context"] if use_expanded else c["text"]
        header = f"[Source {i}: {c['source']} | {c['format']} | score={c['final_score']}]\n"
        block  = header + body + "\n"
        if total + len(block) > limit:
            remaining = limit - total
            if remaining > len(header) + 40:
                parts.append(header + body[: remaining - len(header)] + "…\n")
            break
        parts.append(block)
        total += len(block)

    return "\n".join(parts)
