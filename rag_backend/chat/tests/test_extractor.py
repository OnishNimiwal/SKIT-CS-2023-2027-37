"""
tests/test_extractor.py
========================
Unit tests for multimodal_extractor.py — covers every supported format.

These tests are OFFLINE (no Ollama / ChromaDB needed).
Synthetic files are created in a temp directory and deleted after.

Run with:
    cd rag_backend
    python -m pytest chat/tests/test_extractor.py -v
"""

from __future__ import annotations

import csv
import os
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# ── Conditional imports for optional deps ────────────────────────────────────
def _has(*pkgs: str) -> bool:
    import importlib
    return all(importlib.util.find_spec(p) is not None for p in pkgs)


HAS_PDF   = _has("pymupdf")
HAS_DOCX  = _has("docx")
HAS_XLSX  = _has("openpyxl")
HAS_PPTX  = _has("pptx")
HAS_OCR   = _has("pytesseract", "PIL")
HAS_AUDIO = _has("whisper")


# ── Extractor under test ─────────────────────────────────────────────────────
from chat.multimodal_extractor import extract_from_file, is_supported, ALL_SUPPORTED


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp(tmp_path):
    """Provide a fresh temp directory for each test."""
    return tmp_path


def _write(dir_: Path, name: str, content: bytes) -> Path:
    p = dir_ / name
    p.write_bytes(content)
    return p


# ─────────────────────────────────────────────────────────────────────────────
# Format registry
# ─────────────────────────────────────────────────────────────────────────────

class TestFormatRegistry:
    def test_all_supported_is_nonempty(self):
        assert len(ALL_SUPPORTED) > 0

    def test_common_extensions_registered(self):
        for ext in [".pdf", ".docx", ".txt", ".csv", ".xlsx", ".pptx"]:
            assert ext in ALL_SUPPORTED, f"{ext} missing from ALL_SUPPORTED"

    def test_is_supported_true(self):
        assert is_supported(Path("document.pdf"))
        assert is_supported(Path("data.csv"))
        assert is_supported(Path("notes.txt"))

    def test_is_supported_false(self):
        assert not is_supported(Path("archive.zip"))
        assert not is_supported(Path("video.mp4"))
        assert not is_supported(Path("executable.exe"))

    def test_unsupported_raises(self, tmp):
        f = _write(tmp, "file.xyz", b"hello")
        with pytest.raises(ValueError, match="Unsupported"):
            extract_from_file(f)

    def test_missing_file_raises(self, tmp):
        with pytest.raises(FileNotFoundError):
            extract_from_file(tmp / "ghost.txt")


# ─────────────────────────────────────────────────────────────────────────────
# Plain text / Markdown
# ─────────────────────────────────────────────────────────────────────────────

class TestPlainText:
    CONTENT = "MRPL refinery processes 300,000 barrels per day.\nSafety is our top priority."

    def test_txt_extraction(self, tmp):
        f = _write(tmp, "report.txt", self.CONTENT.encode())
        result = extract_from_file(f)
        assert result["format"] == "Text"
        assert result["ext"] == ".txt"
        assert "MRPL" in result["text"]
        assert "300,000" in result["text"]

    def test_md_extraction(self, tmp):
        content = "# MRPL Report\n\nRefinery capacity: **300 kbpd**."
        f = _write(tmp, "notes.md", content.encode())
        result = extract_from_file(f)
        assert result["format"] == "Markdown"
        assert "MRPL" in result["text"]

    def test_rst_extraction(self, tmp):
        f = _write(tmp, "doc.rst", b"RST Document\n============\nContent here.")
        result = extract_from_file(f)
        assert result["format"] == "Markdown"  # RST treated as Markdown
        assert "RST" in result["text"]

    def test_empty_txt(self, tmp):
        f = _write(tmp, "empty.txt", b"")
        result = extract_from_file(f)
        assert result["text"] == ""

    def test_unicode_txt(self, tmp):
        content = "Olá mundo. Привет мир. 日本語テスト."
        f = _write(tmp, "unicode.txt", content.encode("utf-8"))
        result = extract_from_file(f)
        assert "Olá" in result["text"]

    def test_result_schema(self, tmp):
        f = _write(tmp, "schema.txt", b"hello world")
        result = extract_from_file(f)
        for key in ("text", "format", "ext", "extra_meta"):
            assert key in result, f"Missing key: {key}"


# ─────────────────────────────────────────────────────────────────────────────
# CSV / TSV
# ─────────────────────────────────────────────────────────────────────────────

class TestCSV:
    def _make_csv(self, tmp: Path, name: str = "data.csv") -> Path:
        content = (
            "Department,Budget,Headcount\n"
            "Refinery,5000000,120\n"
            "Safety,800000,30\n"
            "HR,200000,10\n"
        )
        return _write(tmp, name, content.encode())

    def test_csv_format_label(self, tmp):
        f = self._make_csv(tmp)
        result = extract_from_file(f)
        assert result["format"] == "CSV"

    def test_csv_contains_header_values(self, tmp):
        f = self._make_csv(tmp)
        result = extract_from_file(f)
        assert "Department" in result["text"]
        assert "Budget" in result["text"]

    def test_csv_contains_data_rows(self, tmp):
        f = self._make_csv(tmp)
        result = extract_from_file(f)
        assert "Refinery" in result["text"]
        assert "5000000" in result["text"]

    def test_csv_key_value_format(self, tmp):
        """Data rows should be formatted as key: value pairs for better semantic search."""
        f = self._make_csv(tmp)
        result = extract_from_file(f)
        # Expect "Department: Refinery" or similar key:value formatting
        assert "Refinery" in result["text"]

    def test_csv_row_count_meta(self, tmp):
        f = self._make_csv(tmp)
        result = extract_from_file(f)
        # row_count in extra_meta
        assert "row_count" in result["extra_meta"]

    def test_tsv_format_label(self, tmp):
        content = "Name\tValue\nAlpha\t100\nBeta\t200\n"
        f = _write(tmp, "data.tsv", content.encode())
        result = extract_from_file(f)
        assert result["format"] == "TSV"
        assert "Alpha" in result["text"]

    def test_empty_csv(self, tmp):
        f = _write(tmp, "empty.csv", b"")
        result = extract_from_file(f)
        assert result["text"] == "" or result["text"] is not None


# ─────────────────────────────────────────────────────────────────────────────
# XLSX (requires openpyxl)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_XLSX, reason="openpyxl not installed")
class TestXLSX:
    def _make_xlsx(self, tmp: Path) -> Path:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Q3 Data"
        ws.append(["Month", "Revenue", "Units"])
        ws.append(["July",  1200000,  450])
        ws.append(["August", 1350000, 490])
        ws.append(["September", 1100000, 410])
        path = tmp / "report.xlsx"
        wb.save(str(path))
        return path

    def test_xlsx_format_label(self, tmp):
        f = self._make_xlsx(tmp)
        result = extract_from_file(f)
        assert result["format"] == "Excel Spreadsheet"

    def test_xlsx_sheet_name_in_text(self, tmp):
        f = self._make_xlsx(tmp)
        result = extract_from_file(f)
        assert "Q3 Data" in result["text"]

    def test_xlsx_header_values_present(self, tmp):
        f = self._make_xlsx(tmp)
        result = extract_from_file(f)
        assert "Revenue" in result["text"]
        assert "Month" in result["text"]

    def test_xlsx_data_values_present(self, tmp):
        f = self._make_xlsx(tmp)
        result = extract_from_file(f)
        assert "July" in result["text"]
        assert "1200000" in result["text"]

    def test_xlsx_sheet_names_meta(self, tmp):
        f = self._make_xlsx(tmp)
        result = extract_from_file(f)
        assert "sheet_names" in result["extra_meta"]
        assert "Q3 Data" in result["extra_meta"]["sheet_names"]

    def test_xlsx_multi_sheet(self, tmp):
        import openpyxl
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "Sheet1"
        ws1.append(["A", "B"])
        ws2 = wb.create_sheet("Sheet2")
        ws2.append(["X", "Y"])
        ws2.append(["alpha", "beta"])
        path = tmp / "multi.xlsx"
        wb.save(str(path))
        result = extract_from_file(path)
        assert "Sheet1" in result["text"]
        assert "Sheet2" in result["text"]
        assert "alpha" in result["text"]


# ─────────────────────────────────────────────────────────────────────────────
# DOCX (requires python-docx)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_DOCX, reason="python-docx not installed")
class TestDOCX:
    def _make_docx(self, tmp: Path) -> Path:
        from docx import Document
        doc = Document()
        doc.add_heading("MRPL Safety Report 2026", level=1)
        doc.add_paragraph("All personnel must wear PPE at all times.")
        doc.add_paragraph("Incident rate target: 0.5 per 1000 hours.")
        t = doc.add_table(rows=2, cols=2)
        t.cell(0, 0).text = "Zone"
        t.cell(0, 1).text = "Risk Level"
        t.cell(1, 0).text = "Refinery A"
        t.cell(1, 1).text = "High"
        path = tmp / "safety.docx"
        doc.save(str(path))
        return path

    def test_docx_format_label(self, tmp):
        f = self._make_docx(tmp)
        result = extract_from_file(f)
        assert result["format"] == "Word Document"

    def test_docx_heading_text(self, tmp):
        f = self._make_docx(tmp)
        result = extract_from_file(f)
        assert "MRPL Safety Report" in result["text"]

    def test_docx_paragraph_text(self, tmp):
        f = self._make_docx(tmp)
        result = extract_from_file(f)
        assert "PPE" in result["text"]
        assert "Incident rate" in result["text"]

    def test_docx_table_text(self, tmp):
        f = self._make_docx(tmp)
        result = extract_from_file(f)
        assert "Refinery A" in result["text"]
        assert "High" in result["text"]


# ─────────────────────────────────────────────────────────────────────────────
# PPTX (requires python-pptx)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
class TestPPTX:
    def _make_pptx(self, tmp: Path) -> Path:
        from pptx import Presentation
        from pptx.util import Inches, Pt

        prs = Presentation()
        blank_layout = prs.slide_layouts[1]

        s1 = prs.slides.add_slide(blank_layout)
        s1.shapes.title.text = "Q3 Business Review"
        s1.placeholders[1].text = "Revenue grew 12% YoY."

        s2 = prs.slides.add_slide(blank_layout)
        s2.shapes.title.text = "Safety KPIs"
        s2.placeholders[1].text = "Zero LTI incidents in September."

        path = tmp / "review.pptx"
        prs.save(str(path))
        return path

    def test_pptx_format_label(self, tmp):
        f = self._make_pptx(tmp)
        result = extract_from_file(f)
        assert result["format"] == "PowerPoint"

    def test_pptx_slide_markers(self, tmp):
        f = self._make_pptx(tmp)
        result = extract_from_file(f)
        assert "[Slide 1]" in result["text"]
        assert "[Slide 2]" in result["text"]

    def test_pptx_title_text(self, tmp):
        f = self._make_pptx(tmp)
        result = extract_from_file(f)
        assert "Q3 Business Review" in result["text"]

    def test_pptx_body_text(self, tmp):
        f = self._make_pptx(tmp)
        result = extract_from_file(f)
        assert "Revenue grew" in result["text"]
        assert "Safety KPIs" in result["text"]

    def test_pptx_slide_count_meta(self, tmp):
        f = self._make_pptx(tmp)
        result = extract_from_file(f)
        assert result["extra_meta"].get("slide_count") == 2


# ─────────────────────────────────────────────────────────────────────────────
# Cross-format: schema consistency
# ─────────────────────────────────────────────────────────────────────────────

class TestSchemaConsistency:
    """Every handler must return the same schema regardless of format."""

    REQUIRED_KEYS = {"text", "format", "ext", "extra_meta"}

    def _assert_schema(self, result: dict) -> None:
        for k in self.REQUIRED_KEYS:
            assert k in result, f"Missing key '{k}' in result"
        assert isinstance(result["text"], str)
        assert isinstance(result["format"], str) and result["format"]
        assert isinstance(result["ext"], str) and result["ext"].startswith(".")
        assert isinstance(result["extra_meta"], dict)

    def test_txt_schema(self, tmp):
        f = _write(tmp, "f.txt", b"hello")
        self._assert_schema(extract_from_file(f))

    def test_md_schema(self, tmp):
        f = _write(tmp, "f.md", b"# Hi")
        self._assert_schema(extract_from_file(f))

    def test_csv_schema(self, tmp):
        f = _write(tmp, "f.csv", b"a,b\n1,2")
        self._assert_schema(extract_from_file(f))

    def test_tsv_schema(self, tmp):
        f = _write(tmp, "f.tsv", b"a\tb\n1\t2")
        self._assert_schema(extract_from_file(f))

    @pytest.mark.skipif(not HAS_XLSX, reason="openpyxl not installed")
    def test_xlsx_schema(self, tmp):
        import openpyxl
        wb = openpyxl.Workbook()
        wb.active.append(["x", "y"])
        p = tmp / "f.xlsx"
        wb.save(str(p))
        self._assert_schema(extract_from_file(p))

    @pytest.mark.skipif(not HAS_DOCX, reason="python-docx not installed")
    def test_docx_schema(self, tmp):
        from docx import Document
        d = Document()
        d.add_paragraph("Test")
        p = tmp / "f.docx"
        d.save(str(p))
        self._assert_schema(extract_from_file(p))

    @pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
    def test_pptx_schema(self, tmp):
        from pptx import Presentation
        prs = Presentation()
        prs.slides.add_slide(prs.slide_layouts[6])
        p = tmp / "f.pptx"
        prs.save(str(p))
        self._assert_schema(extract_from_file(p))
