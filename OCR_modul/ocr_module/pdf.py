"""PDF ingestion: use the embedded text layer if present, OCR scanned pages otherwise."""
from __future__ import annotations

from typing import Iterator

import fitz  # PyMuPDF
import numpy as np

from .engine import OCREngine


def iter_pdf_pages(
    path: str, engine: OCREngine, dpi: int = 300, min_chars: int = 30
) -> Iterator[dict]:
    """Yield {page, text, method, confidence} for each page of the PDF."""
    with fitz.open(path) as pdf:
        for i, page in enumerate(pdf, start=1):
            text = page.get_text().strip()
            if len(text) >= min_chars:  # digital PDF page
                yield {"page": i, "text": text, "method": "text-layer", "confidence": 100.0}
                continue

            # Scanned page -> render to an image and OCR it
            pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
            result = engine.image_to_result(img)
            yield {"page": i, "text": result.text, "method": "ocr",
                   "confidence": result.confidence}
