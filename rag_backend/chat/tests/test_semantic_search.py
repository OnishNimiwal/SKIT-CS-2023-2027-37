"""
tests/test_semantic_search.py
==============================
Offline unit tests for the semantic search scoring utilities.

Does NOT require Ollama, ChromaDB, or any vector store — only tests
pure-Python scoring helpers (BM25, MMR, keyword extraction, grouping).

These functions are extracted from chat.semantic_search but re-implemented
here inline so the test module has ZERO external dependencies beyond pytest.

Run with:
    python -m pytest chat/tests/test_semantic_search.py -v
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Inline implementations (mirrors chat/semantic_search.py exactly)
# No Django / Ollama / ChromaDB imports — 100% offline
# ─────────────────────────────────────────────────────────────────────────────

_STOPWORDS = frozenset(
    "a an the and or not is are was were be been being have has had do does "
    "did will would could should may might shall can i we you he she it they "
    "in on at to for of with by from up about into through during before after "
    "above below between what who how when where why which this that these those "
    "then than so but if as".split()
)


def _tokenise(text: str) -> list[str]:
    return [
        t.lower() for t in re.findall(r"\b[a-zA-Z0-9_\-]+\b", text)
        if len(t) >= 2
    ]


def _extract_keywords(query: str) -> list[str]:
    return [t for t in _tokenise(query) if t not in _STOPWORDS]


def _bm25_score(
    query_terms: list[str],
    doc_text: str,
    avg_doc_len: float = 300.0,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    tokens = _tokenise(doc_text)
    doc_len = len(tokens)
    tf_map = Counter(tokens)
    score = 0.0
    for term in query_terms:
        tf = tf_map.get(term, 0)
        numerator   = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * doc_len / max(avg_doc_len, 1))
        score += numerator / max(denominator, 1e-9)
    max_possible = (k1 + 1) * len(query_terms) if query_terms else 1
    return min(score / max_possible, 1.0)


def _cosine_text(a: str, b: str) -> float:
    va, vb = Counter(_tokenise(a)), Counter(_tokenise(b))
    keys = set(va) | set(vb)
    if not keys:
        return 0.0
    dot = sum(va.get(k, 0) * vb.get(k, 0) for k in keys)
    mag_a = math.sqrt(sum(v**2 for v in va.values()))
    mag_b = math.sqrt(sum(v**2 for v in vb.values()))
    return dot / max(mag_a * mag_b, 1e-9)


def _mmr_select(candidates: list[dict], top_k: int, lambda_: float = 0.6) -> list[dict]:
    selected: list[dict] = []
    remaining = list(candidates)
    while remaining and len(selected) < top_k:
        if not selected:
            best = max(remaining, key=lambda c: c["final_score"])
        else:
            def mmr_score(c: dict) -> float:
                return lambda_ * c["final_score"] - (1 - lambda_) * max(
                    _cosine_text(c["text"], s["text"]) for s in selected
                )
            best = max(remaining, key=mmr_score)
        selected.append(best)
        remaining.remove(best)
    return selected


def group_by_format(chunks: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list] = defaultdict(list)
    for c in chunks:
        groups[c["format"]].append(c)
    return dict(groups)


def build_context_string(
    chunks: list[dict], max_chars: int = 6000, use_expanded: bool = True
) -> str:
    parts: list[str] = []
    total = 0
    for i, c in enumerate(chunks, 1):
        body   = c.get("context", c["text"]) if use_expanded else c["text"]
        header = f"[Source {i}: {c['source']} | {c['format']} | score={c['final_score']}]\n"
        block  = header + body + "\n"
        if total + len(block) > max_chars:
            remaining = max_chars - total
            if remaining > len(header) + 40:
                parts.append(header + body[: remaining - len(header)] + "…\n")
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Tokeniser & keyword extractor
# ─────────────────────────────────────────────────────────────────────────────

class TestTokeniser:
    def test_basic_split(self):
        assert "mrpl" in _tokenise("MRPL refinery 2026")

    def test_min_length(self):
        tokens = _tokenise("a is of")
        # single-char tokens filtered out (len >= 2)
        assert "a" not in tokens

    def test_numbers_kept(self):
        assert "300000" in _tokenise("capacity 300000 bpd")

    def test_hyphen_kept(self):
        tokens = _tokenise("state-of-the-art system")
        assert "state-of-the-art" in tokens or "state" in tokens

    def test_empty_string(self):
        assert _tokenise("") == []


class TestKeywordExtractor:
    def test_stopwords_removed(self):
        kws = _extract_keywords("What is the refinery capacity?")
        for stop in ("what", "is", "the"):
            assert stop not in kws

    def test_content_words_kept(self):
        kws = _extract_keywords("What is the refinery capacity?")
        assert "refinery" in kws
        assert "capacity" in kws

    def test_all_stopwords(self):
        kws = _extract_keywords("what is the")
        assert kws == []

    def test_mixed_case_lowercased(self):
        kws = _extract_keywords("MRPL Safety Report")
        assert "mrpl" in kws
        assert "safety" in kws


# ─────────────────────────────────────────────────────────────────────────────
# BM25 scorer
# ─────────────────────────────────────────────────────────────────────────────

class TestBM25Score:
    DOC_HIT = "MRPL refinery capacity is 300 000 barrels per day at Mangalore."
    DOC_MISS = "The weather today is sunny and warm."

    def test_hit_score_higher_than_miss(self):
        kws = ["mrpl", "refinery", "capacity"]
        s_hit  = _bm25_score(kws, self.DOC_HIT)
        s_miss = _bm25_score(kws, self.DOC_MISS)
        assert s_hit > s_miss

    def test_score_range(self):
        for doc in (self.DOC_HIT, self.DOC_MISS):
            s = _bm25_score(["mrpl"], doc)
            assert 0.0 <= s <= 1.0

    def test_empty_query(self):
        assert _bm25_score([], self.DOC_HIT) == 0.0

    def test_empty_doc(self):
        s = _bm25_score(["mrpl"], "")
        assert s == 0.0

    def test_multiple_term_hits_higher(self):
        s_one = _bm25_score(["refinery"], self.DOC_HIT)
        s_many = _bm25_score(["refinery", "mrpl", "capacity"], self.DOC_HIT)
        assert s_many >= s_one


# ─────────────────────────────────────────────────────────────────────────────
# Text cosine similarity
# ─────────────────────────────────────────────────────────────────────────────

class TestCosineText:
    def test_identical_texts(self):
        t = "MRPL refinery handles crude oil."
        assert _cosine_text(t, t) == pytest.approx(1.0, abs=0.001)

    def test_disjoint_texts(self):
        a = "apple orange banana"
        b = "quantum physics neutron"
        assert _cosine_text(a, b) == pytest.approx(0.0, abs=0.001)

    def test_partial_overlap(self):
        a = "MRPL refinery crude oil"
        b = "MRPL safety protocol"
        score = _cosine_text(a, b)
        assert 0.0 < score < 1.0

    def test_empty_inputs(self):
        assert _cosine_text("", "") == 0.0
        assert _cosine_text("hello", "") == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# MMR selection
# ─────────────────────────────────────────────────────────────────────────────

def _make_candidate(text: str, score: float, fmt: str = "PDF") -> dict:
    return {
        "text": text,
        "final_score": score,
        "format": fmt,
        "source": "test.pdf",
        "doc_id": "1",
        "chunk_index": 0,
        "format_color": "#ef4444",
        "vector_score": score,
        "bm25_score": 0.0,
        "context": text,
    }


class TestMMRSelect:
    def test_returns_top_k(self):
        candidates = [
            _make_candidate(f"Document text {i}", 0.9 - i * 0.1)
            for i in range(10)
        ]
        selected = _mmr_select(candidates, top_k=4)
        assert len(selected) == 4

    def test_top_scored_included_first(self):
        candidates = [
            _make_candidate("unique text about refinery capacity", 0.95),
            _make_candidate("weather forecast sunshine tomorrow", 0.60),
        ]
        selected = _mmr_select(candidates, top_k=2, lambda_=1.0)
        assert selected[0]["final_score"] == pytest.approx(0.95)

    def test_diversity_avoids_duplicates(self):
        # Two nearly identical high-scoring chunks + one diverse lower-scorer
        dup_text = "MRPL refinery crude oil processing unit large scale"
        candidates = [
            _make_candidate(dup_text, 0.90),
            _make_candidate(dup_text + " additionally", 0.89),
            _make_candidate("Safety protocol personnel PPE equipment", 0.70),
        ]
        # With low lambda (high diversity weight) the diverse chunk should be preferred
        selected = _mmr_select(candidates, top_k=2, lambda_=0.1)
        texts = {c["text"][:20] for c in selected}
        # Should include both the top result AND the diverse one
        assert len(texts) == 2

    def test_fewer_candidates_than_k(self):
        candidates = [_make_candidate("only one", 0.8)]
        selected = _mmr_select(candidates, top_k=5)
        assert len(selected) == 1

    def test_empty_candidates(self):
        assert _mmr_select([], top_k=5) == []


# ─────────────────────────────────────────────────────────────────────────────
# group_by_format
# ─────────────────────────────────────────────────────────────────────────────

class TestGroupByFormat:
    def _chunk(self, fmt: str) -> dict:
        return _make_candidate(f"text from {fmt}", 0.8, fmt)

    def test_groups_correctly(self):
        chunks = [
            self._chunk("PDF"), self._chunk("PDF"),
            self._chunk("CSV"), self._chunk("Excel Spreadsheet"),
        ]
        groups = group_by_format(chunks)
        assert len(groups["PDF"]) == 2
        assert len(groups["CSV"]) == 1
        assert len(groups["Excel Spreadsheet"]) == 1

    def test_empty_input(self):
        assert group_by_format([]) == {}

    def test_single_format(self):
        chunks = [self._chunk("Word Document")] * 3
        groups = group_by_format(chunks)
        assert list(groups.keys()) == ["Word Document"]
        assert len(groups["Word Document"]) == 3


# ─────────────────────────────────────────────────────────────────────────────
# build_context_string
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildContextString:
    def _make_chunks(self, texts: list[str]) -> list[dict]:
        return [
            {**_make_candidate(t, 0.8), "context": t}
            for t in texts
        ]

    def test_includes_all_chunks(self):
        chunks = self._make_chunks(["Chunk A content.", "Chunk B content."])
        ctx = build_context_string(chunks, max_chars=10000)
        assert "Chunk A" in ctx
        assert "Chunk B" in ctx

    def test_respects_max_chars(self):
        # 10 chunks of 500 chars each = 5000 chars; limit to 1000
        chunks = self._make_chunks(["x" * 500] * 10)
        ctx = build_context_string(chunks, max_chars=1000)
        assert len(ctx) <= 1100  # small buffer for headers

    def test_source_and_format_in_header(self):
        chunks = self._make_chunks(["Important data here."])
        ctx = build_context_string(chunks)
        assert "test.pdf" in ctx
        assert "PDF" in ctx

    def test_score_in_header(self):
        chunks = self._make_chunks(["Content."])
        ctx = build_context_string(chunks)
        assert "score=" in ctx

    def test_empty_chunks(self):
        ctx = build_context_string([], max_chars=1000)
        assert ctx == ""
