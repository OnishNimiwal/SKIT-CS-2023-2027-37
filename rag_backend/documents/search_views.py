"""
search_views.py  —  Unified cross-format search endpoint.

GET/POST /api/documents/search/
    query   (str, required)    — the search query
    formats (str, optional)    — comma-separated format filter, e.g. "PDF,CSV"
    doc_ids (str, optional)    — comma-separated doc ID filter
    top_k   (int, optional)    — max results (default 10)

Response JSON:
    {
      "query": "...",
      "total": 4,
      "results": [
        {
          "text":       "...",
          "source":     "report.pdf",
          "doc_id":     "42",
          "chunk_index": 3,
          "format":     "PDF",
          "format_color": "#ef4444",
          "score":      0.8712
        },
        ...
      ]
    }
"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.retrieval import retrieve_chunks


# Format → badge colour mapping (returned so the frontend can render badges)
FORMAT_COLORS: dict[str, str] = {
    "PDF":               "#ef4444",   # red
    "Word Document":     "#3b82f6",   # blue
    "Text":              "#64748b",   # slate
    "Markdown":          "#8b5cf6",   # violet
    "Excel Spreadsheet": "#22c55e",   # green
    "CSV":               "#10b981",   # emerald
    "TSV":               "#14b8a6",   # teal
    "PowerPoint":        "#f97316",   # orange
    "Image (OCR)":       "#f59e0b",   # amber
    "Audio Transcript":  "#6366f1",   # indigo
    "Unknown":           "#94a3b8",   # grey
}


class UnifiedSearchView(APIView):
    """
    Semantic search across ALL indexed documents regardless of format.
    Results are ranked by cosine-similarity score and include format metadata.
    """

    def _parse_params(self, request: Request) -> dict:
        # Support both GET (query params) and POST (body)
        data = request.data if request.method == "POST" else request.query_params

        query = (data.get("query") or data.get("q") or "").strip()

        formats_raw = (data.get("formats") or "").strip()
        formats = [f.strip() for f in formats_raw.split(",") if f.strip()] or None

        doc_ids_raw = (data.get("doc_ids") or "").strip()
        doc_ids = [d.strip() for d in doc_ids_raw.split(",") if d.strip()] or None

        try:
            top_k = int(data.get("top_k", 10))
            top_k = max(1, min(top_k, 50))  # clamp 1..50
        except (TypeError, ValueError):
            top_k = 10

        return {
            "query": query,
            "formats": formats,
            "doc_ids": doc_ids,
            "top_k": top_k,
        }

    def _handle(self, request: Request) -> Response:
        params = self._parse_params(request)
        query = params["query"]

        if not query:
            return Response(
                {"error": "Missing required parameter: 'query' (or 'q')."},
                status=400,
            )

        chunks = retrieve_chunks(
            query=query,
            doc_ids=params["doc_ids"],
            formats=params["formats"],
            top_k=params["top_k"],
        )

        # Enrich results with format colour for UI badges
        enriched = []
        for chunk in chunks:
            fmt = chunk.get("format", "Unknown")
            enriched.append({
                **chunk,
                "format_color": FORMAT_COLORS.get(fmt, FORMAT_COLORS["Unknown"]),
            })

        return Response({
            "query": query,
            "total": len(enriched),
            "filters_applied": {
                "formats": params["formats"],
                "doc_ids": params["doc_ids"],
            },
            "results": enriched,
        })

    def get(self, request: Request) -> Response:
        return self._handle(request)

    def post(self, request: Request) -> Response:
        return self._handle(request)
