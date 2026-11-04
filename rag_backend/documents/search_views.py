"""
search_views.py — Unified cross-format semantic search endpoint.

GET  /api/documents/search/?q=...&formats=PDF,CSV&top_k=10
POST /api/documents/search/  {"query": "...", "formats": "PDF,CSV"}

Response:
    {
      "query": "...",
      "total": 4,
      "filters_applied": {"formats": [...], "doc_ids": [...]},
      "results": [
        {
          "text":          "...",
          "context":       "...",       # expanded text (may be wider than text)
          "source":        "report.pdf",
          "doc_id":        "42",
          "chunk_index":   3,
          "format":        "PDF",
          "format_color":  "#ef4444",
          "vector_score":  0.8900,
          "bm25_score":    0.4200,
          "final_score":   0.8125,
          "score":         0.8125       # alias of final_score for compatibility
        },
        ...
      ]
    }
"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.retrieval import retrieve_chunks, FORMAT_COLORS


class UnifiedSearchView(APIView):
    """
    Semantic search across ALL indexed documents regardless of format.

    Results are ranked by a combined vector-similarity + BM25 score and
    include format metadata so the frontend can render coloured badges.
    """

    def _parse_params(self, request: Request) -> dict:
        data = request.data if request.method == "POST" else request.query_params

        # Accept both "query" and "q" aliases
        query = (data.get("query") or data.get("q") or "").strip()

        formats_raw = (data.get("formats") or "").strip()
        formats = [f.strip() for f in formats_raw.split(",") if f.strip()] or None

        doc_ids_raw = (data.get("doc_ids") or "").strip()
        doc_ids = [d.strip() for d in doc_ids_raw.split(",") if d.strip()] or None

        try:
            top_k = int(data.get("top_k", 10))
            top_k = max(1, min(top_k, 50))
        except (TypeError, ValueError):
            top_k = 10

        return {
            "query":   query,
            "formats": formats,
            "doc_ids": doc_ids,
            "top_k":   top_k,
        }

    def _handle(self, request: Request) -> Response:
        params = self._parse_params(request)
        query  = params["query"]

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

        # Enrich results with format colour + backward-compat "score" alias
        enriched = []
        for chunk in chunks:
            fmt = chunk.get("format", "Unknown")
            enriched.append({
                **chunk,
                "format_color": FORMAT_COLORS.get(fmt, FORMAT_COLORS["Unknown"]),
                "score": chunk.get("final_score", chunk.get("score", 0.0)),
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
