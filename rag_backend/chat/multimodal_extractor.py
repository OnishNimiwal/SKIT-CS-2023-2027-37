"""
multimodal_extractor.py
=======================
Format-aware text extractor for the MRPL AI Workbench.

Supports:
    .pdf   → PyMuPDF
    .docx  → python-docx
    .txt / .md → plain read
    .xlsx  → openpyxl
    .csv   → csv stdlib
    .pptx  → python-pptx
    .png / .jpg / .jpeg / .bmp / .tiff → pytesseract OCR
    .mp3 / .wav / .ogg / .m4a / .flac  → openai-whisper transcription

Every handler returns:
    {
        "text": str,           # full extracted text
        "format": str,         # human-readable format label
        "ext": str,            # file extension (.pdf, etc.)
        "extra_meta": dict,    # format-specific metadata (page count, sheet names…)
    }
"""

from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─── Format registry ────────────────────────────────────────────────────────

TEXT_FORMATS     = {".txt", ".md", ".rst"}
PDF_FORMATS      = {".pdf"}
DOCX_FORMATS     = {".docx"}
XLSX_FORMATS     = {".xlsx", ".xls", ".ods"}
CSV_FORMATS      = {".csv", ".tsv"}
PPTX_FORMATS     = {".pptx", ".ppt"}
IMAGE_FORMATS    = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
AUDIO_FORMATS    = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}

ALL_SUPPORTED = (
    TEXT_FORMATS | PDF_FORMATS | DOCX_FORMATS | XLSX_FORMATS |
    CSV_FORMATS  | PPTX_FORMATS | IMAGE_FORMATS | AUDIO_FORMATS
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_result(text: str, fmt: str, ext: str, **meta: Any) -> dict:
    return {
        "text": text.strip(),
        "format": fmt,
        "ext": ext,
        "extra_meta": meta,
    }


# ─── Per-format extractors ────────────────────────────────────────────────────

def _extract_text(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        logger.warning("TXT read failed for %s: %s", path, exc)
        text = ""
    fmt = "Markdown" if path.suffix.lower() in {".md", ".rst"} else "Text"
    return _make_result(text, fmt, path.suffix.lower())


def _extract_pdf(path: Path) -> dict:
    import pymupdf  # PyMuPDF

    pages: list[str] = []
    with pymupdf.open(str(path)) as pdf:
        page_count = len(pdf)
        for page in pdf:
            pages.append(page.get_text())
    return _make_result(
        "\n\n".join(pages), "PDF", ".pdf",
        page_count=page_count,
    )


def _extract_docx(path: Path) -> dict:
    from docx import Document as DocxDocument

    doc = DocxDocument(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    # also grab table cells
    for table in doc.tables:
        for row in table.rows:
            cell_texts = [c.text.strip() for c in row.cells if c.text.strip()]
            if cell_texts:
                paragraphs.append(" | ".join(cell_texts))
    return _make_result(
        "\n".join(paragraphs), "Word Document", ".docx",
        paragraph_count=len(paragraphs),
    )


def _extract_xlsx(path: Path) -> dict:
    import openpyxl

    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    sheet_texts: list[str] = []
    sheet_names = wb.sheetnames

    for name in sheet_names:
        ws = wb[name]
        rows: list[str] = []
        for row in ws.iter_rows(values_only=True):
            cells = [str(c) for c in row if c is not None and str(c).strip()]
            if cells:
                rows.append(" | ".join(cells))
        if rows:
            sheet_texts.append(f"[Sheet: {name}]\n" + "\n".join(rows))

    wb.close()
    return _make_result(
        "\n\n".join(sheet_texts), "Excel Spreadsheet", path.suffix.lower(),
        sheet_names=sheet_names,
    )


def _extract_csv(path: Path) -> dict:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    rows: list[str] = []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter=delimiter)
            header = None
            for i, row in enumerate(reader):
                if i == 0:
                    header = row
                    rows.append(" | ".join(row))  # include header
                else:
                    if header and len(row) == len(header):
                        # key=value pairs make retrieval more semantic
                        rows.append(", ".join(
                            f"{k}: {v}" for k, v in zip(header, row) if v.strip()
                        ))
                    else:
                        rows.append(" | ".join(c for c in row if c.strip()))
    except Exception as exc:
        logger.warning("CSV read failed for %s: %s", path, exc)
    fmt = "TSV" if path.suffix.lower() == ".tsv" else "CSV"
    return _make_result(
        "\n".join(rows), fmt, path.suffix.lower(),
        row_count=len(rows),
    )


def _extract_pptx(path: Path) -> dict:
    from pptx import Presentation

    prs = Presentation(str(path))
    slides: list[str] = []
    for i, slide in enumerate(prs.slides, 1):
        slide_lines: list[str] = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_lines.append(shape.text.strip())
        if slide_lines:
            slides.append(f"[Slide {i}]\n" + "\n".join(slide_lines))

    return _make_result(
        "\n\n".join(slides), "PowerPoint", ".pptx",
        slide_count=len(prs.slides),
    )


def _extract_image(path: Path) -> dict:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise RuntimeError(
            "pytesseract and Pillow are required for image OCR. "
            "Install them: pip install pytesseract Pillow"
        )
    img = Image.open(str(path))
    text = pytesseract.image_to_string(img)
    return _make_result(
        text, "Image (OCR)", path.suffix.lower(),
        image_size=f"{img.width}x{img.height}",
    )


def _extract_audio(path: Path) -> dict:
    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "openai-whisper is required for audio transcription. "
            "Install it: pip install openai-whisper"
        )
    # Use base model by default — users on-prem can change to small/medium
    model = whisper.load_model("base")
    result = model.transcribe(str(path), fp16=False)
    text = result.get("text", "")
    language = result.get("language", "unknown")
    return _make_result(
        text, "Audio Transcript", path.suffix.lower(),
        language=language,
    )


# ─── Public API ───────────────────────────────────────────────────────────────

def extract_from_file(path: str | Path) -> dict:
    """
    Auto-detect format from file extension and return extracted text + metadata.

    Args:
        path: Absolute path to the file.

    Returns:
        {
            "text": str,
            "format": str,       # e.g. "PDF", "Excel Spreadsheet", "Image (OCR)"
            "ext": str,          # e.g. ".pdf"
            "extra_meta": dict,  # format-specific extras
        }

    Raises:
        ValueError: if the file extension is not supported.
        RuntimeError: if a required optional dependency is missing.
    """
    p = Path(path)
    ext = p.suffix.lower()

    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    if ext in TEXT_FORMATS:
        return _extract_text(p)
    if ext in PDF_FORMATS:
        return _extract_pdf(p)
    if ext in DOCX_FORMATS:
        return _extract_docx(p)
    if ext in XLSX_FORMATS:
        return _extract_xlsx(p)
    if ext in CSV_FORMATS:
        return _extract_csv(p)
    if ext in PPTX_FORMATS:
        return _extract_pptx(p)
    if ext in IMAGE_FORMATS:
        return _extract_image(p)
    if ext in AUDIO_FORMATS:
        return _extract_audio(p)

    raise ValueError(
        f"Unsupported file format: '{ext}'. "
        f"Supported: {', '.join(sorted(ALL_SUPPORTED))}"
    )


def is_supported(path: str | Path) -> bool:
    """Return True if the file extension is supported by this extractor."""
    return Path(path).suffix.lower() in ALL_SUPPORTED
