"""RAG building blocks — extended for multimodal ingestion.

Supports:
    PDF, DOCX, TXT, MD, XLSX, CSV, PPTX, Images (OCR), Audio (Whisper)

All formats are chunked, embedded via OllamaEmbeddings, and stored in
ChromaDB with rich metadata so cross-format search works seamlessly.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.conf import settings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .multimodal_extractor import extract_from_file, is_supported

logger = logging.getLogger(__name__)


# ─── Vector store singleton ─────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    embeddings = OllamaEmbeddings(
        model=settings.OLLAMA_EMBED_MODEL,
        base_url=settings.OLLAMA_URL,
    )
    return Chroma(
        collection_name="documents",
        embedding_function=embeddings,
        persist_directory=str(settings.VECTOR_DB_DIR),
        collection_metadata={"hnsw:space": "cosine"},  # relevance scores 0..1
    )


# ─── Text splitter ───────────────────────────────────────────────────────────

def _get_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=getattr(settings, "CHUNK_SIZE", 800),
        chunk_overlap=getattr(settings, "CHUNK_OVERLAP", 120),
        separators=["\n\n", "\n", ". ", " ", ""],
    )


# ─── Ingestion ───────────────────────────────────────────────────────────────

def ingest_file(path: str, doc_id: str) -> int:
    """
    Ingest any supported file into ChromaDB.

    1. Extract text (format-aware).
    2. Split into overlapping chunks.
    3. Attach rich metadata: {doc_id, source, format, ext, chunk_index, …}.
    4. Embed and upsert into ChromaDB.

    Returns the number of chunks stored.
    """
    p = Path(path)

    if not is_supported(p):
        raise ValueError(f"File type not supported: {p.suffix}")

    # ── Extract ──────────────────────────────────────────────────────────────
    extracted = extract_from_file(p)
    raw_text: str = extracted["text"]
    fmt: str = extracted["format"]
    ext: str = extracted["ext"]
    extra_meta: dict = extracted["extra_meta"]

    if not raw_text.strip():
        logger.warning("No text extracted from %s (%s)", p.name, fmt)
        return 0

    # ── Split ────────────────────────────────────────────────────────────────
    splitter = _get_splitter()
    chunks_text = splitter.split_text(raw_text)

    # ── Build LangChain Documents ────────────────────────────────────────────
    docs: list[Document] = []
    ids: list[str] = []

    for i, chunk in enumerate(chunks_text):
        chunk_id = f"{doc_id}__chunk{i}"
        meta: dict[str, Any] = {
            "doc_id": str(doc_id),
            "source": p.name,
            "format": fmt,
            "ext": ext,
            "chunk_index": i,
        }
        # Flatten extra_meta — Chroma only stores str/int/float/bool
        for k, v in extra_meta.items():
            if isinstance(v, (str, int, float, bool)):
                meta[k] = v
            elif isinstance(v, (list, tuple)):
                meta[k] = ", ".join(str(x) for x in v)

        docs.append(Document(page_content=chunk, metadata=meta))
        ids.append(chunk_id)

    # ── Upsert into ChromaDB ─────────────────────────────────────────────────
    vs = get_vectorstore()
    vs.add_documents(documents=docs, ids=ids)

    logger.info(
        "Ingested %s: %d chunks | format=%s | doc_id=%s",
        p.name, len(docs), fmt, doc_id,
    )
    return len(docs)


def delete_document(doc_id: str) -> None:
    """Remove all chunks for a given doc_id from ChromaDB."""
    vs = get_vectorstore()
    existing = vs.get(where={"doc_id": str(doc_id)})
    ids_to_delete = existing.get("ids", [])
    if ids_to_delete:
        vs.delete(ids=ids_to_delete)
        logger.info("Deleted %d chunks for doc_id=%s", len(ids_to_delete), doc_id)
    else:
        logger.warning("No chunks found for doc_id=%s", doc_id)


# ─── Legacy compatibility ────────────────────────────────────────────────────
# The original extract_text() was used by older views. Keep it for backward compat.

def extract_text(path: str) -> str:
    """Return raw text from a file. Uses the multimodal extractor."""
    try:
        result = extract_from_file(path)
        return result["text"]
    except Exception as exc:
        logger.error("extract_text failed for %s: %s", path, exc)
        return ""
