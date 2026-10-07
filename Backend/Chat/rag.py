"""RAG building blocks: ingestion (chunk + embed + store) and retrieval."""

from functools import lru_cache
from pathlib import Path

from django.conf import settings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


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
        collection_metadata={"hnsw:space": "cosine"},  # makes relevance scores 0..1
    )


def extract_text(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".pdf":
        import pymupdf
        with pymupdf.open(str(p)) as pdf:
            return "\n".join(page.get_text() for page in pdf)

    if suffix == ".docx":
        from docx import Document as DocxDocument
        d = DocxDocument(str(p))
        parts = [para.text for para in d.paragraphs]
        for table in d.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(parts)

    return p.read_text(encoding="utf-8", errors="ignore")


def ingest_file(path: str, doc_id, filename: str) -> int:
    """Chunk, embed and store a file. Returns the number of chunks."""
    text = extract_text(path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = [c for c in splitter.split_text(text) if c.strip()]
    docs = [
        Document(
            page_content=c,
            metadata={"doc_id": str(doc_id), "source": filename, "chunk": i},
        )
        for i, c in enumerate(chunks)
    ]
    if docs:
        get_vectorstore().add_documents(
            docs, ids=[f"{doc_id}-{i}" for i in range(len(docs))]
        )
    return len(docs)


def delete_document(doc_id) -> None:
    get_vectorstore().delete(where={"doc_id": str(doc_id)})


def retrieve(query: str, doc_ids: list[str] | None = None):
    """Top-k chunks above the relevance threshold, optionally limited to some documents."""
    flt = {"doc_id": {"$in": [str(d) for d in doc_ids]}} if doc_ids else None
    results = get_vectorstore().similarity_search_with_relevance_scores(
        query, k=settings.RAG_TOP_K, filter=flt
    )
    return [doc for doc, score in results if score >= settings.RAG_MIN_SCORE]