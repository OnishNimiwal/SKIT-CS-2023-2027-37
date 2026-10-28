"""Retrieval grading: decide whether the retrieved context is good enough."""

import re

from django.conf import settings

GOOD = "good"    # best chunk is confidently relevant
WEAK = "weak"    # chunks found, but none is a confident match
EMPTY = "empty"  # nothing relevant found


def grade_chunks(chunks: list[dict], good_score: float | None = None) -> str:
    if not chunks:
        return EMPTY
    if good_score is None:
        good_score = getattr(settings, "RAG_GOOD_SCORE", 0.4)
    best = max(c["score"] for c in chunks)
    return GOOD if best >= good_score else WEAK


def decide_next_step(verdict: str, attempts: int, max_retries: int | None = None) -> str:
    """
    good                         -> generate
    weak/empty, retries left     -> rewrite the query and search again
    weak, no retries left        -> generate with the best available context
    empty, no retries left       -> not_found
    """
    if max_retries is None:
        max_retries = getattr(settings, "RAG_MAX_RETRIES", 1)
    if verdict == GOOD:
        return "generate"
    if attempts < max_retries:
        return "rewrite"
    return "generate" if verdict == WEAK else "not_found"


def clean_query(text: str, fallback: str) -> str:
    """Tidy an LLM-rewritten search query (first line, no label or quotes)."""
    lines = [ln for ln in (text or "").strip().splitlines() if ln.strip()]
    if not lines:
        return fallback
    query = re.sub(r"^(search query|query)\s*:\s*", "", lines[0].strip(), flags=re.IGNORECASE)
    query = query.strip(" \t\"'`")
    return query[:200] or fallback