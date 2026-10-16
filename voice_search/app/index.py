"""Turn a transcript into timestamped chunks, embed them, store in local Chroma, and search."""
from __future__ import annotations

import uuid
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

from . import config, stt


@lru_cache(maxsize=1)
def get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )


_store: Optional[Chroma] = None


def get_store() -> Chroma:
    global _store
    if _store is None:
        _store = Chroma(
            collection_name=config.CHROMA_COLLECTION,
            embedding_function=get_embeddings(),
            persist_directory=str(config.CHROMA_DIR),
            collection_metadata={"hnsw:space": "cosine"},
        )
    return _store


def set_store(store: Chroma) -> None:
    """Replace the store (used by tests)."""
    global _store
    _store = store


def group_segments(segments: List[stt.Segment]) -> List[Dict]:
    """Merge neighbouring segments into chunks of ~CHUNK_SECONDS / CHUNK_MAX_CHARS,
    keeping the start and end time of each chunk so a hit can seek the audio."""
    chunks: List[Dict] = []
    cur: List[stt.Segment] = []

    def flush():
        if cur:
            chunks.append(
                {"start": cur[0].start, "end": cur[-1].end, "text": " ".join(s.text for s in cur)}
            )
            cur.clear()

    for seg in segments:
        cur.append(seg)
        too_long = seg.end - cur[0].start >= config.CHUNK_SECONDS
        too_big = sum(len(s.text) for s in cur) >= config.CHUNK_MAX_CHARS
        if too_long or too_big:
            flush()
    flush()
    return chunks


def index_audio(path: Path, filename: str, doc_id: str) -> Dict:
    """Transcribe -> chunk -> embed -> store. Returns a summary including the full transcript."""
    transcript = stt.transcribe(path)
    chunks = group_segments(transcript.segments)
    if not chunks:
        raise ValueError("No speech detected in this recording.")

    docs = [
        Document(
            page_content=c["text"],
            metadata={
                "doc_id": doc_id, "source": filename, "file": path.name,
                "start": c["start"], "end": c["end"], "chunk": i,
                "language": transcript.language,
            },
        )
        for i, c in enumerate(chunks)
    ]
    get_store().add_documents(docs, ids=[f"{doc_id}-{i}" for i in range(len(docs))])
    return {
        "doc_id": doc_id,
        "filename": filename,
        "language": transcript.language,
        "duration": transcript.duration,
        "chunks": len(chunks),
        "transcript": chunks,
    }


def _hit(doc: Document, score: float) -> Dict:
    m = doc.metadata
    return {
        "doc_id": m["doc_id"], "filename": m["source"], "file": m["file"],
        "start": m["start"], "end": m["end"], "language": m["language"],
        "score": round(float(score), 3), "text": doc.page_content,
    }


def search(query: str, k: int = config.TOP_K, doc_id: Optional[str] = None) -> List[Dict]:
    flt = {"doc_id": doc_id} if doc_id else None
    hits = get_store().similarity_search_with_relevance_scores(query, k=k, filter=flt)
    return [_hit(d, s) for d, s in hits]


def get_transcript(doc_id: str) -> List[Dict]:
    data = get_store().get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
    rows = sorted(zip(data["metadatas"], data["documents"]), key=lambda r: r[0]["chunk"])
    return [{"start": m["start"], "end": m["end"], "text": t} for m, t in rows]


def list_files() -> List[Dict]:
    agg: Dict[str, Dict] = defaultdict(lambda: {"chunks": 0, "duration": 0.0})
    for m in get_store().get(include=["metadatas"])["metadatas"]:
        a = agg[m["doc_id"]]
        a.update(doc_id=m["doc_id"], filename=m["source"], file=m["file"], language=m["language"])
        a["chunks"] += 1
        a["duration"] = max(a["duration"], m["end"])
    return sorted(agg.values(), key=lambda x: x["filename"])


def delete_file(doc_id: str) -> int:
    ids = get_store().get(where={"doc_id": doc_id})["ids"]
    if ids:
        get_store().delete(ids=ids)
    return len(ids)


def new_id() -> str:
    return uuid.uuid4().hex[:12]
