"""Updated documents/urls.py — adds the unified /search/ endpoint."""

from django.urls import path
from .views import DocumentListCreateView, DocumentDetailView
from .search_views import UnifiedSearchView

urlpatterns = [
    # List all documents / upload new document
    path("",      DocumentListCreateView.as_view(), name="document-list-create"),

    # Retrieve or delete a single document
    path("<int:pk>/", DocumentDetailView.as_view(), name="document-detail"),

    # ── NEW: Cross-format semantic search ──────────────────────────────────
    # GET  /api/documents/search/?q=query&formats=PDF,CSV&top_k=10
    # POST /api/documents/search/  {"query": "...", "formats": "PDF,CSV"}
    path("search/", UnifiedSearchView.as_view(), name="document-unified-search"),
]
