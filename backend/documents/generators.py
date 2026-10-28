import io
from datetime import datetime
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

def generate_document_docx_report(document, summary_text: str = "") -> io.BytesIO:
    """
    Generates a professional Word document (.docx) report for a given Document instance.
    Returns an in-memory BytesIO buffer.
    """
    doc = docx.Document()

    # Document Margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Title Header
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("MRPL AI Workbench")
    title_run.font.name = "Arial"
    title_run.font.size = Pt(22)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(37, 99, 235)  # Primary blue

    subtitle_p = doc.add_paragraph()
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = subtitle_p.add_run("Local Document Analysis & AI Report")
    sub_run.font.name = "Arial"
    sub_run.font.size = Pt(13)
    sub_run.font.italic = True
    sub_run.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph()  # Spacer

    # Document Metadata Heading
    h2 = doc.add_heading("1. Document Metadata", level=2)
    h2.runs[0].font.name = "Arial"
    h2.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    # Metadata Table
    table = doc.add_table(rows=5, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    metadata_rows = [
        ("Filename:", document.original_name),
        ("File Type:", document.file_type),
        ("Uploaded At:", document.uploaded_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
        ("Extracted Characters:", f"{len(document.extracted_text):,} characters"),
        ("Processing Server:", "PC5 (Strictly On-Premise Local Inference)"),
    ]

    for i, (label, val) in enumerate(metadata_rows):
        row = table.rows[i]
        # Label cell
        cell_lbl = row.cells[0]
        cell_lbl.width = Inches(2.2)
        p_lbl = cell_lbl.paragraphs[0]
        run_lbl = p_lbl.add_run(label)
        run_lbl.font.bold = True
        run_lbl.font.size = Pt(10)
        run_lbl.font.color.rgb = RGBColor(71, 85, 105)

        # Value cell
        cell_val = row.cells[1]
        cell_val.width = Inches(4.3)
        p_val = cell_val.paragraphs[0]
        run_val = p_val.add_run(val)
        run_val.font.size = Pt(10)
        run_val.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph()  # Spacer

    # AI Summary Section
    h2_sum = doc.add_heading("2. Local AI Executive Summary", level=2)
    h2_sum.runs[0].font.name = "Arial"
    h2_sum.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    if summary_text and summary_text.strip():
        for paragraph_text in summary_text.strip().split("\n\n"):
            if paragraph_text.strip():
                p = doc.add_paragraph()
                p_run = p.add_run(paragraph_text.strip())
                p_run.font.name = "Arial"
                p_run.font.size = Pt(10.5)
                p_run.font.color.rgb = RGBColor(30, 41, 59)
    else:
        p_empty = doc.add_paragraph()
        p_empty_run = p_empty.add_run("(No summary was requested for this report export.)")
        p_empty_run.font.italic = True
        p_empty_run.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph()  # Spacer

    # Extracted Text Section
    h2_text = doc.add_heading("3. Extracted Document Content", level=2)
    h2_text.runs[0].font.name = "Arial"
    h2_text.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    # Add text paragraphs (limit to first 10,000 characters for docx preview if large)
    preview_text = document.extracted_text
    is_truncated = False
    if len(preview_text) > 15000:
        preview_text = preview_text[:15000]
        is_truncated = True

    for block in preview_text.split("\n\n"):
        if block.strip():
            p_block = doc.add_paragraph()
            p_block_run = p_block.add_run(block.strip())
            p_block_run.font.name = "Arial"
            p_block_run.font.size = Pt(9.5)
            p_block_run.font.color.rgb = RGBColor(51, 65, 85)

    if is_truncated:
        p_trunc = doc.add_paragraph()
        run_trunc = p_trunc.add_run(
            "[... Content preview truncated in report. Full content stored in MRPL AI Workbench database ...]"
        )
        run_trunc.font.italic = True
        run_trunc.font.color.rgb = RGBColor(148, 163, 184)

    # Footer
    footer = doc.sections[0].footer
    footer_p = footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer_run = footer_p.add_run(
        f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC | MRPL Confidential - Local On-Premise"
    )
    footer_run.font.size = Pt(8)
    footer_run.font.color.rgb = RGBColor(148, 163, 184)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
