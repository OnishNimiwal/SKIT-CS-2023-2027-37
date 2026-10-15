"""LangChain integration: turns images / scanned PDFs into `Document` objects
that the embedding + vector-store stages of the RAG pipeline can consume."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, List

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from .engine import OCREngine
from .pdf import iter_pdf_pages

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
PDF_EXTS = {".pdf"}


class OCRDocumentLoader(BaseLoader):
    """Load a single image or PDF (scanned or digital) as LangChain Documents."""

    def __init__(self, file_path: str, engine: OCREngine | None = None):
        self.file_path = Path(file_path)
        self.engine = engine or OCREngine()

    def lazy_load(self) -> Iterator[Document]:
        ext = self.file_path.suffix.lower()
        source = str(self.file_path)

        if ext in IMAGE_EXTS:
            res = self.engine.image_to_result(str(self.file_path))
            if res.text:
                yield Document(
                    page_content=res.text,
                    metadata={"source": source, "modality": "image", "page": 1,
                              "ocr_confidence": res.confidence,
                              "word_count": res.word_count},
                )
        elif ext in PDF_EXTS:
            for p in iter_pdf_pages(source, self.engine):
                if p["text"]:
                    yield Document(
                        page_content=p["text"],
                        metadata={"source": source, "modality": "pdf", "page": p["page"],
                                  "extraction_method": p["method"],
                                  "ocr_confidence": p["confidence"]},
                    )
        else:
            raise ValueError(f"Unsupported file type: {ext}")


def load_documents(path: str, engine: OCREngine | None = None) -> List[Document]:
    """Load a file, or every supported file in a folder (recursive)."""
    engine = engine or OCREngine()
    p = Path(path)
    files = (
        [f for f in sorted(p.rglob("*")) if f.suffix.lower() in IMAGE_EXTS | PDF_EXTS]
        if p.is_dir() else [p]
    )
    docs: List[Document] = []
    for f in files:
        docs.extend(OCRDocumentLoader(str(f), engine).load())
    return docs
