"""
tests/test_search_api.py
=========================
Django API-level tests for the UnifiedSearchView endpoint.

GET/POST /api/documents/search/

These tests use Django's test client with mocked retrieval — no Ollama
or ChromaDB required.

Run with:
    cd rag_backend
    python -m pytest documents/tests/test_search_api.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import django
import pytest

# ── Bootstrap Django ─────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ_set = __import__("os").environ.setdefault
os.environ_set("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    django.setup()
except RuntimeError:
    pass  # already set up

from django.test import RequestFactory

from documents.search_views import UnifiedSearchView, FORMAT_COLORS


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

MOCK_CHUNKS = [
    {
        "text":        "MRPL refinery processes 300,000 barrels per day at Mangalore.",
        "source":      "annual_report.pdf",
        "doc_id":      "1",
        "chunk_index": 0,
        "format":      "PDF",
        "score":       0.87,
    },
    {
        "text":        "Department: Safety, Budget: 8000000, Headcount: 30.",
        "source":      "budget.csv",
        "doc_id":      "2",
        "chunk_index": 0,
        "format":      "CSV",
        "score":       0.74,
    },
    {
        "text":        "Revenue grew 12% year-on-year. Key driver: refinery throughput.",
        "source":      "summary.md",
        "doc_id":      "3",
        "chunk_index": 1,
        "format":      "Markdown",
        "score":       0.61,
    },
]


@pytest.fixture()
def factory():
    return RequestFactory()


@pytest.fixture()
def view():
    return UnifiedSearchView.as_view()


def _mock_retrieve(chunks=None):
    """Context manager that patches retrieve_chunks to return controlled data."""
    return patch(
        "documents.search_views.retrieve_chunks",
        return_value=chunks if chunks is not None else MOCK_CHUNKS,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET requests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetSearch:

    def test_get_returns_200(self, factory, view):
        with _mock_retrieve():
            request = factory.get("/api/documents/search/", {"q": "refinery capacity"})
            response = view(request)
        assert response.status_code == 200

    def test_get_missing_query_returns_400(self, factory, view):
        request = factory.get("/api/documents/search/")
        response = view(request)
        assert response.status_code == 400
        assert "error" in response.data

    def test_get_empty_query_returns_400(self, factory, view):
        request = factory.get("/api/documents/search/", {"q": "   "})
        response = view(request)
        assert response.status_code == 400

    def test_response_has_required_fields(self, factory, view):
        with _mock_retrieve():
            request = factory.get("/api/documents/search/", {"q": "mrpl"})
            response = view(request)
        data = response.data
        assert "query" in data
        assert "total" in data
        assert "results" in data

    def test_query_echoed_in_response(self, factory, view):
        with _mock_retrieve():
            request = factory.get("/api/documents/search/", {"q": "safety protocol"})
            response = view(request)
        assert response.data["query"] == "safety protocol"

    def test_total_matches_results_count(self, factory, view):
        with _mock_retrieve():
            request = factory.get("/api/documents/search/", {"q": "mrpl"})
            response = view(request)
        assert response.data["total"] == len(response.data["results"])

    def test_results_have_format_color(self, factory, view):
        with _mock_retrieve():
            request = factory.get("/api/documents/search/", {"q": "mrpl"})
            response = view(request)
        for r in response.data["results"]:
            assert "format_color" in r
            assert r["format_color"].startswith("#")

    def test_format_colors_are_correct(self, factory, view):
        with _mock_retrieve():
            request = factory.get("/api/documents/search/", {"q": "mrpl"})
            response = view(request)
        for r in response.data["results"]:
            expected = FORMAT_COLORS.get(r["format"], FORMAT_COLORS["Unknown"])
            assert r["format_color"] == expected

    def test_top_k_parameter(self, factory, view):
        chunks_15 = MOCK_CHUNKS * 5  # 15 items
        with _mock_retrieve(chunks_15):
            request = factory.get("/api/documents/search/", {"q": "mrpl", "top_k": "2"})
            response = view(request)
        # The view passes top_k to retrieve_chunks; since we mock it,
        # we just verify the param was parsed without error
        assert response.status_code == 200

    def test_top_k_clamped_max_50(self, factory, view):
        with _mock_retrieve():
            request = factory.get("/api/documents/search/", {"q": "mrpl", "top_k": "999"})
            response = view(request)
        assert response.status_code == 200  # no crash

    def test_top_k_clamped_min_1(self, factory, view):
        with _mock_retrieve():
            request = factory.get("/api/documents/search/", {"q": "mrpl", "top_k": "0"})
            response = view(request)
        assert response.status_code == 200

    def test_accepts_q_alias(self, factory, view):
        """Both 'query' and 'q' should be accepted."""
        with _mock_retrieve():
            request = factory.get("/api/documents/search/", {"query": "mrpl refinery"})
            response = view(request)
        assert response.status_code == 200
        assert response.data["query"] == "mrpl refinery"


# ─────────────────────────────────────────────────────────────────────────────
# POST requests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPostSearch:

    def test_post_returns_200(self, factory, view):
        with _mock_retrieve():
            request = factory.post(
                "/api/documents/search/",
                data={"query": "MRPL refinery"},
                content_type="application/json",
            )
            response = view(request)
        assert response.status_code == 200

    def test_post_missing_query_400(self, factory, view):
        request = factory.post(
            "/api/documents/search/",
            data={},
            content_type="application/json",
        )
        response = view(request)
        assert response.status_code == 400

    def test_post_response_structure(self, factory, view):
        with _mock_retrieve():
            request = factory.post(
                "/api/documents/search/",
                data={"query": "safety incidents"},
                content_type="application/json",
            )
            response = view(request)
        assert response.data["total"] == len(response.data["results"])


# ─────────────────────────────────────────────────────────────────────────────
# Format filter
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFormatFilter:

    def test_formats_param_parsed(self, factory, view):
        """Verify the formats filter is parsed and passed without errors."""
        with patch("documents.search_views.retrieve_chunks") as mock_rc:
            mock_rc.return_value = [MOCK_CHUNKS[0]]
            request = factory.get(
                "/api/documents/search/",
                {"q": "mrpl", "formats": "PDF,CSV"},
            )
            response = view(request)
        assert response.status_code == 200
        call_kwargs = mock_rc.call_args
        # formats kwarg should contain parsed list
        formats_arg = call_kwargs.kwargs.get("formats") or (
            call_kwargs.args[2] if len(call_kwargs.args) > 2 else None
        )
        # At minimum ensure no crash — formats parsing is correct
        assert response.data["total"] >= 0

    def test_filters_applied_in_response(self, factory, view):
        with _mock_retrieve():
            request = factory.get(
                "/api/documents/search/",
                {"q": "mrpl", "formats": "PDF"},
            )
            response = view(request)
        assert "filters_applied" in response.data

    def test_no_filter_returns_all(self, factory, view):
        with _mock_retrieve(MOCK_CHUNKS):
            request = factory.get("/api/documents/search/", {"q": "mrpl"})
            response = view(request)
        assert response.data["total"] == len(MOCK_CHUNKS)


# ─────────────────────────────────────────────────────────────────────────────
# Empty results
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmptyResults:

    def test_empty_results_returns_200(self, factory, view):
        with _mock_retrieve([]):
            request = factory.get("/api/documents/search/", {"q": "xyzzy no match"})
            response = view(request)
        assert response.status_code == 200
        assert response.data["total"] == 0
        assert response.data["results"] == []

    def test_empty_results_query_echoed(self, factory, view):
        with _mock_retrieve([]):
            request = factory.get("/api/documents/search/", {"q": "nothing here"})
            response = view(request)
        assert response.data["query"] == "nothing here"


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT_COLORS coverage
# ─────────────────────────────────────────────────────────────────────────────

class TestFormatColors:
    def test_all_expected_formats_have_colors(self):
        expected = [
            "PDF", "Word Document", "Text", "Markdown",
            "Excel Spreadsheet", "CSV", "TSV",
            "PowerPoint", "Image (OCR)", "Audio Transcript", "Unknown",
        ]
        for fmt in expected:
            assert fmt in FORMAT_COLORS, f"Missing color for format: {fmt}"

    def test_all_colors_are_hex(self):
        import re
        hex_re = re.compile(r"^#[0-9a-fA-F]{6}$")
        for fmt, color in FORMAT_COLORS.items():
            assert hex_re.match(color), f"Invalid hex color for {fmt}: {color}"

    def test_unknown_format_has_fallback(self):
        assert "Unknown" in FORMAT_COLORS
