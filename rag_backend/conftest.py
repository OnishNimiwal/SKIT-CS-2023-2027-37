"""
conftest.py — pytest bootstrap for rag_backend tests.

Configures a minimal Django environment so tests can run without
a full server setup. Only needed for offline unit tests that import
from chat.* or documents.*

If Django is not installed, unit tests that don't need it still run.
"""

import os
import sys
from pathlib import Path

# ── Add rag_backend to sys.path so "chat.*" imports work ─────────────────────
RAG_BACKEND = Path(__file__).resolve().parent
if str(RAG_BACKEND) not in sys.path:
    sys.path.insert(0, str(RAG_BACKEND))

# ── Bootstrap minimal Django settings ────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    import django
    django.setup()
except Exception:
    # Django not installed — API-level tests will be skipped automatically
    pass
