# -*- coding: utf-8 -*-
"""Builds the SRS for the MRPL AI Workbench, following the chapter structure of
SRS_Transformer-Based_WAF_chapter_headings_edited.docx, with content, tables and
diagrams specific to the SKIT-CS-2023-2027-37 repository.
"""
import os
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(__file__)
FIG = os.path.join(HERE, "figures")
OUT = os.path.join(HERE, "SRS_MRPL_AI_Workbench.docx")

NAVY = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x5F, 0x63, 0x68)

doc = Document()

# ── base styles ──────────────────────────────────────────────────────────────
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

for i, size, before, after in [(1, 20, 18, 6), (2, 15, 14, 4), (3, 12.5, 10, 3)]:
    h = doc.styles[f"Heading {i}"]
    h.font.name = "Calibri"
    h.font.size = Pt(size)
    h.font.bold = True
    h.font.color.rgb = NAVY
    h.paragraph_format.space_before = Pt(before)
    h.paragraph_format.space_after = Pt(after)

def set_cell_shading(cell, hex_color):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(shd)

def add_table(rows, col_widths=None, header=True, font_size=9.5):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = t.rows[r].cells[c]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            run.font.size = Pt(font_size)
            if r == 0 and header:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                set_cell_shading(cell, "2F6FDB")
            elif r % 2 == 0:
                set_cell_shading(cell, "F2F6FD")
        if col_widths:
            for c, w in enumerate(col_widths):
                t.rows[r].cells[c].width = Inches(w)
    doc.add_paragraph()
    return t

def add_figure(path, caption, width=6.3):
    doc.add_picture(os.path.join(FIG, path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(caption)
    run.italic = True
    run.font.size = Pt(9.5)
    run.font.color.rgb = GREY
    doc.add_paragraph()

def add_bullets(items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")

def h1(text):
    doc.add_heading(text, level=1)

def h2(text):
    doc.add_heading(text, level=2)

def h3(text):
    doc.add_heading(text, level=3)

def para(text, italic=False, bold=False, size=11, color=None, align=None):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    run = p.add_run(text)
    run.italic = italic
    run.bold = bold
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    return p

def page_break():
    doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ═════════════════════════════════════════════════════════════════════════
para("A Software Requirements Specification", bold=True, size=20, align=WD_ALIGN_PARAGRAPH.CENTER)
para("On", align=WD_ALIGN_PARAGRAPH.CENTER)
para("MRPL AI Workbench: An On-Premise Multimodal Retrieval-Augmented\nDocument Intelligence Platform",
     bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph()
para("Prepared as a structural analogue of the department's SRS template, reverse-engineered from "
     "the project repository (SKIT-CS-2023-2027-37) rather than from a classroom brief.",
     italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=10.5, color=GREY)
doc.add_paragraph()
doc.add_paragraph()
t = add_table([
    ["MENTOR:", "SUBMITTED BY:"],
    ["[mentor name — to be filled in]", "Onish Nimiwal (onishnimiwalsci@gmail.com)"],
    ["[Associate Professor / designation]", "Mohit Prasoya"],
    ["(Computer Science & Engineering)", "Priyanhu Khariwal"],
    ["", "Rajat Yadav"],
    ["COORDINATOR:", ""],
    ["[coordinator name — to be filled in]", "(roll numbers and section — to be filled in)"],
], header=False, font_size=10.5)
para("Names above are the repository's actual Git contributors (see .mailmap); roll numbers, "
     "mentor and coordinator are placeholders for you to complete.", italic=True, size=9, color=GREY)
doc.add_paragraph()
para("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
para("[Institute name — to be filled in]", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
para("SESSION 2026-27", align=WD_ALIGN_PARAGRAPH.CENTER)
page_break()

# ═════════════════════════════════════════════════════════════════════════
# INDEX
# ═════════════════════════════════════════════════════════════════════════
h2("INDEX")
index_items = [
    "1. Introduction",
    "    1.1 Purpose",
    "    1.2 Need / Motivation",
    "2. Market Survey",
    "    2.1 Objectives",
    "3. Requirements",
    "    3.1 Functional Requirements",
    "    3.2 Non-Functional Requirements",
    "    3.3 Hardware Requirements",
    "    3.4 Software Requirements",
    "    3.5 Agile Model",
    "    3.6 Project Metrics (Repository Evidence)",
    "4. System Architecture",
    "    4.1 Client-Server Architecture",
    "5. Design and Implementation",
    "    5.1 Product Features",
    "    5.2 Data Flow Diagram",
    "    5.3 E-R Diagram",
    "    5.4 Class Diagram",
    "    5.5 Use Case Diagram",
    "    5.6 Sequence Diagram",
    "6. Conclusion & Future Scope",
    "7. Mapping with UN Sustainable Development Goals",
    "Appendix A: Requirement Traceability and Acceptance Checklist",
]
for it in index_items:
    para(it)
page_break()

# ═════════════════════════════════════════════════════════════════════════
# CHAPTER 1 — INTRODUCTION
# ═════════════════════════════════════════════════════════════════════════
h1("Chapter-1  Introduction")
h2("1. Introduction")
para(
    "Enterprises increasingly need to question their own documents instead of re-reading them: incident "
    "reports, vendor manuals, inspection PDFs, spreadsheets of readings, and scanned forms. Sending that "
    "material to a cloud AI service is often not acceptable, because the documents contain internal, "
    "sometimes safety- or compliance-sensitive information. A system is needed that gives the convenience "
    "of a chat assistant without the data ever leaving the organisation's own network."
)
para(
    "MRPL AI Workbench is a software system built to meet that need. It is an on-premise, privacy-compliant "
    "AI chat and document assistant designed for internal corporate deployment on a single server (referred "
    "to in the project as PC5) with access from local workstations (PC2, PC3, PC4) over the local LAN. It "
    "combines a Django REST backend, a React single-page frontend, and a locally hosted Ollama model "
    "(qwen3:4b for generation, nomic-embed-text for embeddings) so that no request, document or answer ever "
    "leaves the local network."
)
para(
    "The repository contains two generations of the backend. The first (backend/) implements Phase 1 general "
    "chat and Phase 2 document assistant: a user signs in, uploads a PDF or TXT file, and asks questions "
    "answered from the whole extracted text (capped at 50,000 characters), with a Word (.docx) report export. "
    "The second (rag_backend/) is a Phase 3 rewrite that replaces \"paste the whole document into the prompt\" "
    "with genuine retrieval-augmented generation: files of many formats (PDF, DOCX, XLSX, CSV, PPTX, images via "
    "OCR, audio via Whisper) are chunked, embedded and stored in a ChromaDB vector store, and a LangGraph "
    "workflow condenses the question, retrieves the most relevant chunks with a hybrid vector + BM25 + MMR "
    "ranking, and asks Ollama to answer strictly from those passages with numbered citations."
)
para(
    "This document is the Software Requirements Specification (SRS) of the project. It is written directly "
    "from the project's own repository — its code, its Git history, its tests and its README — rather than "
    "from a specification written in advance, and it follows the chapter structure used by the department's "
    "standard SRS template so that it reads as a companion document to that format. It describes what the "
    "system does, how well it does it, the environment it needs, the development model that was actually "
    "followed (reconstructed from the commit history), and the architecture and design of the two backends."
)
h2("1.1 Purpose")
para(
    "The purpose of this SRS is to give an accurate, independently reverse-engineered description of the MRPL "
    "AI Workbench so that the project team, a mentor, and an evaluator share one understanding of what the "
    "system currently does — as opposed to what the README alone claims. Every requirement, diagram and table "
    "in this document is grounded in a specific file, class or test in the repository; where the two backends "
    "disagree with each other, or where the README is ahead of or behind the code, this is called out rather "
    "than smoothed over."
)
para(
    "Scope of the system. The system covers the path from a signed-in user's chat message or uploaded "
    "document to an answer, a summary, a cross-format search result, or a downloadable Word report. It "
    "includes session-based authentication, multi-format text extraction, chunking and embedding, hybrid "
    "retrieval, grounded generation through a local LLM, report generation, and a React dashboard. It does "
    "not include a reverse proxy or WAF-style enforcement layer (there is no protected third-party "
    "application in front of it — the Workbench itself is the application users interact with), and it does "
    "not inspect network traffic; its only external interface is the browser-to-Django HTTP/JSON API."
)
para("Intended audience.")
add_bullets([
    "Project team members (Onish Nimiwal, Mohit Prasoya, Priyanhu Khariwal, Rajat Yadav), who designed, "
    "implemented and tested the two backends, the frontend, and the OCR/voice modules.",
    "Mentor and evaluators, who review the work against this specification.",
    "Employees of the organisation deploying the Workbench, who would use it day to day.",
    "Future maintainers, who need to understand why backend/ and rag_backend/ currently coexist and what "
    "each one promises.",
])
para(
    "Methodology. The project followed an incremental Agile approach, reconstructed here from the Git "
    "history rather than asserted (Section 3.5): Phase 1/2 chat and document Q&A first, then session login "
    "and OCR, then a push to make Ollama responses faster, then a from-scratch RAG backend (retrieval, "
    "prompts, context budget, LangGraph), a voice-search module, multimodal ChromaDB ingestion, a per-user "
    "document privacy fix, a dashboard/multimodal-upload feature branch, and finally retrieval grading, "
    "guardrails and a 160-test suite for the RAG backend."
)

t = add_table([
    ["Term", "Meaning"],
    ["RAG", "Retrieval-Augmented Generation"],
    ["LLM", "Large Language Model"],
    ["DRF", "Django REST Framework"],
    ["CORS", "Cross-Origin Resource Sharing"],
    ["CSRF", "Cross-Site Request Forgery"],
    ["LAN", "Local Area Network"],
    ["BM25", "Best Matching 25 — a classic keyword-ranking formula"],
    ["MMR", "Maximal Marginal Relevance — a diversity-aware re-ranking method"],
    ["OCR", "Optical Character Recognition"],
    ["STT", "Speech-to-Text"],
    ["DFD", "Data Flow Diagram"],
    ["ER", "Entity-Relationship"],
    ["SRS", "Software Requirements Specification"],
    ["CI/CD", "Continuous Integration and Continuous Delivery"],
], col_widths=[1.6, 4.9])
para("Table 1.1: Definitions and abbreviations used in this document", italic=True, size=9.5, color=GREY)

h2("1.2 Need / Motivation")
para("The need for this project is visible directly in the repository's own history and design choices.")
add_bullets([
    "Documents outnumber any one format. The multimodal extractor (chat/multimodal_extractor.py) supports "
    "PDF, DOCX, TXT/MD, XLSX, CSV/TSV, PPTX, images and audio — evidence that a single-format assistant was "
    "judged insufficient from early on.",
    "Pasting a whole document into a prompt does not scale. Phase 1/2 (backend/) caps extracted text at "
    "50,000 characters and answers from the whole blob; Phase 3 (rag_backend/) replaces this with chunking, "
    "embedding and top-k retrieval specifically so that only the relevant passages reach the model.",
    "Privacy cannot be bolted on afterwards. ALLOW_EXTERNAL_AI=False, an Ollama URL hard-wired to "
    "127.0.0.1, and a commit titled \"make documents private to the user who uploaded them\" (25/10/2026) "
    "show privacy and per-user isolation being treated as first-class requirements, not afterthoughts.",
    "Irrelevant or hallucinated answers erode trust. The system prompt in rag_backend/chat/prompts.py "
    "explicitly instructs the model to use only the numbered context passages, cite them as [1]/[2], and say "
    "when it cannot find an answer — and a guards.py module filters out small talk before it ever reaches "
    "retrieval.",
    "Quality has to be verifiable, not just claimed. The project carries 200 automated test functions across "
    "its modules (Section 3.6), including dedicated tests for BM25 scoring, MMR diversification and ChromaDB "
    "integration — far beyond what a demo would need.",
])
para(
    "The need can be summarised as follows: the system should (1) accept documents in whatever format an "
    "employee actually has, (2) answer questions grounded only in that material, with citations, (3) keep "
    "every document, prompt and answer inside the local network, (4) keep each user's documents private to "
    "them, and (5) remain testable and auditable as it grows."
)
page_break()

# ═════════════════════════════════════════════════════════════════════════
# CHAPTER 2 — MARKET SURVEY
# ═════════════════════════════════════════════════════════════════════════
h1("Chapter-2  Market Survey")
h2("2. Market Survey")
para(
    "Before describing the requirements, it is useful to place the Workbench against the kinds of document-AI "
    "products that exist. The comparison below is based on the publicly known characteristics of each category "
    "and on the project's own README and code, not on a formal benchmarking exercise."
)
t = add_table([
    ["Solution", "Type", "Grounding method", "Strength", "Limitation"],
    ["Cloud chat assistants\n(e.g. hosted LLM products)", "SaaS", "Large context window\nor vendor RAG", "No infrastructure to run;\nvery capable models",
     "Documents leave the organisation; recurring\ncost; no control over data retention"],
    ["Cloud notebook / document\nQ&A tools", "SaaS", "Vendor-side RAG\nover uploaded files", "Polished UI;\nfast to adopt",
     "Same data-residency concern; limited\ncontrol over chunking, citations or model"],
    ["Open-source local-LLM\nchat UIs (generic)", "Self-hosted", "Whole-document\nin context", "Self-hosted,\nfree",
     "No real retrieval; large documents are\ntruncated or exceed the context window"],
    ["Plain keyword search\nover a file share", "In-house", "Keyword match\n(no ranking by meaning)", "Simple,\nno GPU needed",
     "Misses paraphrases; no answer synthesis;\nno citation of the matching passage"],
    ["MRPL AI Workbench\n(this project)", "Self-hosted,\nopen", "Hybrid vector + BM25 +\nMMR retrieval, local LLM", "Zero external calls; per-user privacy;\nmulti-format; citations; 200 tests",
     "Needs a local GPU/CPU budget for Ollama;\ntwo backend generations currently coexist"],
], col_widths=[1.35, 0.8, 1.3, 1.5, 1.6])
para("Table 2.1: Comparative study of similar solutions", italic=True, size=9.5, color=GREY)

para("Technology trends observed in the repository itself:")
add_bullets([
    "Local-first LLM serving through Ollama is now practical on a single office PC (qwen3:4b, 4-billion "
    "parameters), removing the main historical argument for sending data to the cloud.",
    "Hybrid retrieval (dense vector similarity plus a lexical score such as BM25) has become the default "
    "pattern for RAG, because pure vector search misses exact codes, IDs and acronyms — exactly why the "
    "project added bm25_weight scoring in semantic_search.py.",
    "Graph-based orchestration (LangGraph) is replacing ad-hoc prompt chaining for anything with branching "
    "logic — here, the condense → retrieve → generate/not_found flow in rag_backend/chat/graph.py.",
    "Multimodal ingestion (OCR for scans, speech-to-text for recordings) is increasingly expected rather "
    "than a nice-to-have, reflected in the OCR_modul/ and voice_search/ side-projects feeding into the "
    "same extractor registry.",
])
para(
    "Research gap. Academic RAG papers typically demonstrate a retrieval or re-ranking technique in "
    "isolation; most open-source \"chat with your PDF\" repositories demonstrate a single format and a single "
    "user. This project's gap-filling contribution is combining per-user authentication, multi-format "
    "ingestion, hybrid retrieval and a documented test suite in one deployable Django + React platform, "
    "entirely offline."
)
h2("2.1 Objectives")
add_bullets([
    "To accept and extract text from PDF, DOCX, TXT/MD, XLSX, CSV/TSV, PPTX, image (OCR) and audio "
    "(speech-to-text) files through one common extractor interface.",
    "To chunk and embed extracted text into a local ChromaDB vector store using OllamaEmbeddings "
    "(nomic-embed-text).",
    "To answer questions with a hybrid vector + BM25 + MMR retrieval pipeline, expanding adjacent chunks "
    "for context and returning numbered citations.",
    "To provide a REST API for chat (/api/chat/), document upload/list/detail/ask/summary/report "
    "(/api/documents/*) and unified cross-format search (/api/documents/search/).",
    "To restrict every endpoint to a signed-in user and keep each user's own documents private (Phase 1/2).",
    "To generate an executive summary and a downloadable Word (.docx) report for any uploaded document.",
    "To provide a React dashboard with chat, document upload/list/viewer and a unified search UI.",
    "To keep the system fully on-premise: no call ever leaves 127.0.0.1 for inference, and ALLOW_EXTERNAL_AI "
    "defaults to False.",
    "To verify the system with an automated test suite (200 test functions at the time of writing) covering "
    "extraction, scoring, retrieval and the Django API layer.",
])
page_break()

# ═════════════════════════════════════════════════════════════════════════
# CHAPTER 3 — REQUIREMENTS
# ═════════════════════════════════════════════════════════════════════════
h1("Chapter-3  Requirements")
h2("3. Requirements")
para(
    "This chapter lists the requirements of the MRPL AI Workbench as evidenced by its two backends. Each "
    "requirement has a unique identifier for traceability (Appendix A). Priority is M (Must), S (Should) or "
    "C (Could). Where backend/ and rag_backend/ implement a requirement differently, both are described; "
    "where only one of them does, this is stated rather than implied."
)
h2("3.1 Functional Requirements")
t = add_table([
    ["ID", "Requirement", "Priority"],
    ["FR-1.1", "The system shall require a signed-in session for every API endpoint except login, logout, "
               "CSRF and the current-user check (backend/config/settings.py, accounts app).", "M"],
    ["FR-1.2", "The system shall accept a chat message and return a generated reply from the local Ollama "
               "model (POST /api/chat/).", "M"],
    ["FR-1.3", "The system shall accept an uploaded PDF or TXT file, validate its extension, extract its "
               "text with PyMuPDF/native read, and cap the stored text at 50,000 characters "
               "(backend/documents/extractors.py).", "M"],
    ["FR-1.4", "The system shall answer a question grounded in a specific uploaded document's extracted "
               "text (POST /api/documents/<id>/ask/).", "M"],
    ["FR-1.5", "The system shall generate a structured executive summary of an uploaded document "
               "(POST /api/documents/<id>/summary/).", "M"],
    ["FR-1.6", "The system shall generate and stream a downloadable Word (.docx) report combining metadata, "
               "summary and an extracted-text preview (documents/generators.py).", "S"],
    ["FR-1.7", "The system shall restrict each user to listing, viewing, questioning and deleting only the "
               "documents they themselves uploaded (owner foreign key + get_user_document, backend/).", "M"],
], col_widths=[0.8, 4.9, 0.6])
para("Table 3.1: Authentication, upload and Phase 1/2 document assistant", italic=True, size=9.5, color=GREY)

t = add_table([
    ["ID", "Requirement", "Priority"],
    ["FR-2.1", "The system shall extract text from PDF, DOCX, TXT, MD, XLSX, CSV/TSV, PPTX, image and audio "
               "files through one format registry (chat/multimodal_extractor.py, ALL_SUPPORTED).", "M"],
    ["FR-2.2", "The system shall split extracted text into overlapping chunks (default 800 characters, "
               "120 overlap) and attach metadata (doc_id, source, format, chunk_index) to each chunk "
               "(chat/rag.py).", "M"],
    ["FR-2.3", "The system shall embed each chunk with OllamaEmbeddings and store it in a persistent "
               "ChromaDB collection using cosine similarity (chat/rag.py: get_vectorstore).", "M"],
    ["FR-2.4", "The system shall retrieve the most relevant chunks for a query using a weighted combination "
               "of vector similarity and a BM25-style keyword score (chat/semantic_search.py).", "M"],
    ["FR-2.5", "The system shall diversify the retrieved chunks with Maximal Marginal Relevance (MMR) so "
               "that results are not all drawn from one paragraph (_mmr_select).", "S"],
    ["FR-2.6", "The system shall expand each selected chunk with its immediate neighbours before building "
               "the prompt context, so answers are not cut mid-sentence (_expand_context).", "S"],
    ["FR-2.7", "The system shall rewrite a multi-turn follow-up question into a standalone question before "
               "retrieval (condense_node, rag_backend/chat/graph.py).", "S"],
    ["FR-2.8", "The system shall reply with a fixed \"not found\" message, and no citations, when retrieval "
               "returns no chunks (route() → not_found_node).", "M"],
    ["FR-2.9", "The system shall filter out greetings, thanks and help requests before running retrieval, and "
               "reply to them directly (chat/guards.py).", "S"],
    ["FR-2.10", "The system shall expose a unified cross-format search endpoint that filters by format and/or "
               "document id and returns a combined score (documents/search_views.py).", "S"],
], col_widths=[0.8, 4.9, 0.6])
para("Table 3.2: Multimodal ingestion and retrieval-augmented generation (Phase 3 / rag_backend)",
     italic=True, size=9.5, color=GREY)

t = add_table([
    ["ID", "Requirement", "Priority"],
    ["FR-3.1", "The system shall provide a React single-page app with Chat, Documents and Dashboard tabs "
               "(frontend/src/App.jsx).", "M"],
    ["FR-3.2", "The system shall let a user drag-and-drop or browse for a file to upload and show its "
               "ingestion/embedding status.", "M"],
    ["FR-3.3", "The system shall show the document's extracted text, a Q&A box and a generated summary in a "
               "single workspace view (DocumentViewer.jsx).", "S"],
    ["FR-3.4", "The system shall provide a unified search component that queries across all of a user's "
               "ingested documents regardless of format (UnifiedSearch.jsx).", "S"],
    ["FR-3.5", "The system shall display on-premise / privacy indicators (deployment mode, model name, "
               "external-API status) in the header, consistent with settings.py.", "C"],
    ["FR-3.6", "The system shall support a login page and show the signed-in user's identity "
               "(LoginPage.jsx, accounts API).", "M"],
], col_widths=[0.8, 4.9, 0.6])
para("Table 3.3: Frontend and user experience", italic=True, size=9.5, color=GREY)

h2("3.2 Non-Functional Requirements")
para(
    "The values below are design targets, most already enforced in settings or tests at the time of "
    "writing; they are not independently benchmarked performance numbers."
)
t = add_table([
    ["ID", "Attribute", "Requirement"],
    ["NFR-1", "Performance", "Ollama is kept warm with OLLAMA_KEEP_ALIVE (default 30 m) and Qwen3 \"thinking\" "
              "is disabled by default, a change the project measured as cutting response time from "
              "10–60 s to 0.2–3 s (settings.py comment, commit \"perf: faster AI responses\")."],
    ["NFR-2", "Context budget", "Retrieved context is fit to a character budget (RAG_MAX_CONTEXT_CHARS, "
              "default 6,000) and conversation history is trimmed to the last N messages/chars before every "
              "call, so prompts never silently exceed the model's window (chat/context.py)."],
    ["NFR-3", "Availability", "A retrieval failure (e.g. ChromaDB unavailable) is caught and treated as zero "
              "chunks rather than a hard error, so chat still answers; an unreachable Ollama returns HTTP 503 "
              "rather than crashing the request (chat/views.py, both backends)."],
    ["NFR-4", "Privacy", "ALLOW_EXTERNAL_AI defaults to False; OLLAMA_URL defaults to 127.0.0.1; uploaded "
              "files are not served from a public /media/ URL in backend/ (urls.py comment)."],
    ["NFR-5", "Access control", "Every DRF view requires IsAuthenticated by default in backend/ "
              "(REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES); session cookies are HttpOnly and SameSite=Lax."],
    ["NFR-6", "Usability", "The dashboard works over the LAN from PC2–PC4 via Vite's 0.0.0.0 host binding "
              "and a configurable CORS_ALLOWED_ORIGINS list."],
    ["NFR-7", "Maintainability", "Each backend is split into focused Django apps (accounts, chat, documents) "
              "with one responsibility per module (extractors, services, generators, serializers, views)."],
    ["NFR-8", "Portability", "SQLite requires no separate database server; the stack runs on Windows and "
              "Linux; ChromaDB persists to a local vector_db/ directory."],
    ["NFR-9", "Testability", "The project carries 200 automated test functions at the time of writing "
              "(Section 3.6), including dedicated offline unit tests for scoring utilities that need no "
              "live Ollama or ChromaDB."],
    ["NFR-10", "Observability", "Ingestion logs chunk counts and format per file; semantic_search logs query, "
              "candidate and result counts (logger.info in chat/semantic_search.py)."],
], col_widths=[0.8, 1.3, 4.2])
para("Table 3.4: Non-functional requirements", italic=True, size=9.5, color=GREY)

h2("3.3 Hardware Requirements")
t = add_table([
    ["Component", "Development / demonstration", "With local embeddings + LLM (PC5)", "Small team deployment"],
    ["Processor", "Quad-core, 2.5 GHz or higher", "6–8 core CPU (or GPU for Ollama)", "4 vCPU or higher"],
    ["Memory", "8 GB", "16 GB or higher (qwen3:4b + nomic-embed-text\nresident via keep_alive)", "8–16 GB"],
    ["GPU", "Not required", "Optional — speeds up Ollama generation\nand embedding noticeably", "Optional"],
    ["Storage", "5 GB free", "20 GB free (model weights, vector_db/,\nmedia/, db.sqlite3)", "20 GB SSD"],
    ["Network", "Not required (fully local)", "Local LAN only (PC2–PC4 to PC5)", "100 Mbps LAN or higher"],
], col_widths=[1.1, 1.8, 2.5, 1.3])
para("Table 3.5: Hardware requirements", italic=True, size=9.5, color=GREY)

h2("3.4 Software Requirements")
t = add_table([
    ["Category", "Software"],
    ["Operating system", "Windows 10/11, Ubuntu 22.04 or later"],
    ["Language and runtime", "Python 3.10+ (backend/requirements.txt pins Django 6.1.1); Node.js for the "
                             "Vite/React frontend"],
    ["AI inference", "Ollama (local daemon, port 11434); models qwen3:4b (generation), "
                     "nomic-embed-text (embeddings)"],
    ["RAG stack (rag_backend)", "langchain-core, langchain-ollama, langchain-chroma, langchain-text-splitters, "
                                "langgraph, chromadb"],
    ["Document extraction", "pymupdf (PDF), python-docx (DOCX/report), openpyxl (XLSX), python-pptx (PPTX), "
                            "csv (stdlib), pytesseract + Pillow (OCR), openai-whisper (audio)"],
    ["Backend", "Django, Django REST Framework, django-cors-headers, python-dotenv, requests"],
    ["Frontend", "React 18, Vite, Lucide React icons"],
    ["Database / vector store", "SQLite (relational), ChromaDB (vector_db/, cosine similarity)"],
    ["Testing", "Django's built-in test runner (backend/), pytest + pytest-django + conftest.py "
                "(rag_backend/)"],
    ["CI/CD", "Git, GitHub Actions (.github/workflows/auto_weekly_report.yml)"],
    ["Browser", "Current version of Chrome, Edge or Firefox"],
], col_widths=[1.6, 4.9])
para("Table 3.6: Software requirements", italic=True, size=9.5, color=GREY)

h2("3.5 Agile Model")
para(
    "The project followed an incremental Agile approach. Unlike a specification written before the fact, "
    "the sprint plan below is reconstructed directly from the repository's commit history (git log "
    "--reverse), so it describes what was actually built, in the order it was actually built, rather than "
    "an idealised plan. The scope visibly grew sprint over sprint: Phase 1 chat and Phase 2 document "
    "assistant shipped first, and the RAG rewrite, OCR module, voice-search module and dashboard upload "
    "feature were added as separate, independently testable increments."
)
t = add_table([
    ["Sprint", "Dates", "Goal", "Representative commits"],
    ["1", "11/09/2026", "Phase 1 chat + Phase 2 document\nassistant bootstrap", "\"Initial commit: MRPL AI Workbench "
          "- Phase 1 Chat & Phase 2 Document Assistant\"; architecture docs added to README"],
    ["2", "30/09/2026", "Frontend shell", "\"Add frontend: sidebar, dashboard, i18n, styles, UI smoke test\""],
    ["3", "02–09/10/2026", "Session auth + OCR +\nCI reporting", "\"Add home page and login/logout with session "
          "authentication\"; \"Add OCR module\"; \"ci: add automated Form-3 weekly reporting workflow\""],
    ["4", "14/10/2026", "Home page polish +\nresponse latency", "\"perf: faster AI responses by disabling Qwen3 "
          "thinking and keeping model loaded\""],
    ["5", "15–16/10/2026", "RAG backend scaffold +\nvoice search", "\"feat(retrieval): add scored, deduplicated "
          "document retrieval\"; \"feat(graph): use retrieval, prompts and context in the RAG flow\"; "
          "\"Add voice search module with Whisper speech-to-text\""],
    ["6", "22/10/2026", "Multimodal ChromaDB\ningestion pipeline", "\"feat: add multimodal search with ChromaDB "
          "vector embeddings\"; \"feat: define RAGState for LangGraph workflow\""],
    ["7", "25–26/10/2026", "Per-user privacy fix +\ndashboard/upload feature", "\"fix(security): make documents "
          "private to the user who uploaded them\"; \"Add dashboard and multimodal upload feature\""],
    ["8", "28/10–04/11/2026", "Guardrails, grading,\nsemantic search + 100+ tests", "\"feat(workflow): add input "
          "validation and small-talk routing\"; \"feat(search): add semantic search engine with BM25 + MMR "
          "scoring\"; \"test(extractor): 41 unit tests...\"; \"config(test): add pytest.ini and conftest.py\""],
], col_widths=[0.5, 1.1, 1.5, 3.2])
para("Table 3.7: Sprint plan, reconstructed from Git history (git log --reverse, measured 04/11/2026)",
     italic=True, size=9.5, color=GREY)
para(
    "Across sprints, source code was kept in a Git repository (4 active contributors plus GitHub Actions "
    "automation) with feature branches merged back into main, so each increment could be reviewed and "
    "reverted independently; this is visible directly in the branch list "
    "(feature/dashboard-uploads, feature/dashboard-uploads-v2, mohit, mohit-backup)."
)

h2("3.6 Project Metrics (Repository Evidence)")
para(
    "Unlike a proposal written before any code exists, this project already has a measurable history. The "
    "four charts below are not design targets — they are counted directly from the repository as it stands "
    "on 04/11/2026, and are included so that this SRS's claims (test coverage, team contribution, module "
    "size, format coverage) are checkable rather than asserted."
)
add_figure("graph_3_1_tests_by_module.png", "Figure 3.1: Automated test functions by module.")
add_figure("graph_3_2_commits_by_contributor.png", "Figure 3.2: Commits by contributor.")
add_figure("graph_3_3_repo_composition.png", "Figure 3.3: Tracked files per top-level directory.")
add_figure("graph_3_4_format_taxonomy.png",
           "Figure 3.4: Cross-format taxonomy and colour coding, taken verbatim from the FORMAT_COLORS "
           "dictionary in chat/semantic_search.py — the same colours the dashboard would use to badge a "
           "search result by source format.")
page_break()

# ═════════════════════════════════════════════════════════════════════════
# CHAPTER 4 — SYSTEM ARCHITECTURE
# ═════════════════════════════════════════════════════════════════════════
h1("Chapter-4  System Architecture")
h2("4. System Architecture")
para(
    "The system follows a layered design in which every layer has one responsibility and talks to the next "
    "through a well-defined interface. A request enters the React SPA, is sent to the Django REST API, is "
    "processed by the extraction/retrieval pipeline, is answered by the local Ollama model, and the result "
    "is returned to the browser and (where relevant) persisted to SQLite, ChromaDB or local disk. The layers "
    "are:"
)
add_bullets([
    "Presentation layer: the React + Vite SPA (Chat, Documents, Dashboard, Login).",
    "Service layer: the Django REST Framework application — accounts, chat and documents apps, exposing "
    "session auth, chat and document endpoints.",
    "Processing layer: the multi-format extractor, text splitter and (in rag_backend) the chunk/metadata "
    "builder.",
    "Intelligence layer: the local Ollama daemon (qwen3:4b for generation, nomic-embed-text for embeddings) "
    "and, in rag_backend, the LangGraph condense/retrieve/generate workflow with hybrid BM25+vector+MMR "
    "scoring.",
    "Storage layer: SQLite (users, document metadata), ChromaDB (chunks and vectors, rag_backend only) and "
    "local disk (media/documents/).",
])
add_figure("fig_4_0_context.png",
           "Figure 4.0: The Workbench sits between LAN users and the local Ollama engine — the system owns "
           "its own AI engine rather than enforcing a decision in front of a separate protected application.")

h2("4.1 Client-Server Architecture")
para(
    "The system uses a client-server architecture inside a single trusted LAN. The client is the browser of "
    "an employee or administrator on PC2, PC3 or PC4; the server is the Django REST API and, behind it, the "
    "Ollama daemon, both running on PC5. Communication between the browser and the API uses HTTP with "
    "session cookies and CSRF protection on write requests; communication between Django and Ollama uses "
    "plain HTTP to 127.0.0.1:11434 with a 120-second timeout."
)
add_figure("fig_4_1_client_server.png", "Figure 4.1: Client-Server Architecture.")

t = add_table([
    ["Component", "Technology", "Responsibility"],
    ["Browser", "Any modern browser on PC2–PC4", "Renders the React SPA; holds the session cookie"],
    ["React SPA", "React 18, Vite, Lucide icons", "Chat, Documents and Dashboard UI; calls /api/*"],
    ["Django REST API", "Django 6, DRF, django-cors-headers", "Session auth, chat, documents, unified search "
     "endpoints; :8000"],
    ["Extractor / splitter", "PyMuPDF, python-docx, openpyxl,\npython-pptx, pytesseract, openai-whisper", "Converts any "
     "supported file to plain text, optionally chunked"],
    ["Embeddings + vector store", "OllamaEmbeddings (nomic-embed-text),\nChromaDB", "Stores and retrieves chunk "
     "vectors with cosine similarity (rag_backend only)"],
    ["LLM", "Ollama daemon, qwen3:4b", "Generates chat replies, summaries and grounded answers; :11434, "
     "bound to 127.0.0.1"],
    ["Relational store", "SQLite (db.sqlite3)", "Users, sessions, document metadata"],
    ["Report generator", "python-docx", "Builds the downloadable .docx executive report"],
], col_widths=[1.5, 2.1, 3.1])
para("Table 4.1: Components and responsibilities", italic=True, size=9.5, color=GREY)

t = add_table([
    ["Group", "Endpoints", "Purpose"],
    ["Auth", "GET /api/auth/csrf/, POST /api/auth/login/,\nPOST /api/auth/logout/, GET /api/auth/me/",
     "Session cookie, sign-in, sign-out, current user"],
    ["Chat (Phase 1)", "POST /api/chat/", "General-purpose chat reply from Ollama (and, in rag_backend, "
     "the full RAG graph)"],
    ["Documents (Phase 2)", "POST /api/documents/upload/, GET /api/documents/,\nGET/DELETE "
     "/api/documents/<id>/, POST /api/documents/<id>/ask/,\nPOST /api/documents/<id>/summary/, "
     "POST /api/documents/<id>/generate-report/", "Upload, list, inspect, question, summarise and export "
     "a single document"],
    ["Documents (Phase 3)", "GET/POST /api/documents/ (list/create),\nGET/DELETE /api/documents/<id>/,\n"
     "GET/POST /api/documents/search/", "Multimodal ingestion and unified cross-format semantic search"],
], col_widths=[1.3, 2.9, 2.5])
para("Table 4.2: API groups exposed by the two backends", italic=True, size=9.5, color=GREY)
para(
    "Deployment view. For local use, Django runs on port 8000 and Vite on port 5173; for LAN access, "
    "Vite is started with --host 0.0.0.0 and Django's ALLOWED_HOSTS/CORS are opened to the local network. "
    "Only one of backend/ or rag_backend/ is intended to run at a time against the same frontend, since they "
    "expose incompatible document schemas (Section 5.3)."
)
page_break()

# ═════════════════════════════════════════════════════════════════════════
# CHAPTER 5 — DESIGN AND IMPLEMENTATION
# ═════════════════════════════════════════════════════════════════════════
h1("Chapter-5  Design and Implementation")
h2("5. Design and Implementation")
para(
    "This chapter describes what the system offers to its users and how it is designed, using the same "
    "standard notations as the department's SRS template: data flow diagrams (DFD), an entity-relationship "
    "(E-R) diagram, a class diagram, a use case diagram and a sequence diagram — each one drawn from the "
    "actual modules and functions named in the repository rather than from a generic template."
)
h2("5.1 Product Features")
t = add_table([
    ["Feature", "Description"],
    ["Session-based sign-in", "Every API call requires a signed-in session; accounts are created by an "
     "administrator (createsuperuser / Django admin)."],
    ["General chat (Phase 1)", "A free-form chat endpoint backed directly by the local Ollama model."],
    ["Document upload & extraction", "PDF/TXT (Phase 1/2) or PDF, DOCX, TXT/MD, XLSX, CSV/TSV, PPTX, image "
     "and audio (Phase 3) files are parsed into plain text."],
    ["Document-grounded Q&A", "Questions are answered from a specific document's text (Phase 1/2) or from "
     "retrieved chunks across one or more documents (Phase 3)."],
    ["Executive summary", "A structured overview, key points and conclusion generated from a document."],
    ["Word report export", "A downloadable .docx combining metadata, summary and an extracted-text preview."],
    ["Hybrid semantic search", "Vector similarity (OllamaEmbeddings) combined with a BM25-style keyword "
     "score and MMR diversification."],
    ["Cross-format unified search", "One query searches PDFs, spreadsheets, presentations, images and audio "
     "transcripts together, with a colour-coded format badge."],
    ["Context-budgeted prompts", "Retrieved chunks and chat history are trimmed to a character budget before "
     "every call to the local LLM, so prompts never silently overflow."],
    ["Guarded small talk", "Greetings, thanks and help requests are answered directly, without spending a "
     "retrieval pass."],
    ["Per-user document privacy", "Backend/ documents carry an owner foreign key; a user can only list, "
     "read, question or delete their own documents."],
    ["Fully on-premise inference", "ALLOW_EXTERNAL_AI=False by default; Ollama is only ever called at "
     "127.0.0.1."],
    ["Automated test suite", "200 test functions across both backends and the OCR/voice modules "
     "(Section 3.6), including an offline test module that re-implements the scoring functions with zero "
     "external dependencies so they can run without Ollama or ChromaDB."],
    ["Weekly Form-3 progress report", "A GitHub Actions workflow regenerates a PDF progress report from "
     "the Git history of all branches every Thursday."],
], col_widths=[1.9, 4.8])
para("Table 5.1: Product features", italic=True, size=9.5, color=GREY)

h2("5.2 Data Flow Diagram")
para(
    "DFD-0 (context diagram). The whole system is one process, MRPL AI Workbench. Unlike a WAF sitting in "
    "front of someone else's application, this system IS the application the user interacts with, so the "
    "external entities are simply the signed-in Employee/User (sends messages, uploads and questions) and "
    "the System Administrator (creates accounts through the Django admin, a separate, lower-traffic "
    "interaction)."
)
add_figure("fig_5_1_dfd0.png", "Figure 5.1: DFD level 0 (context diagram).")

para(
    "DFD-1 (main processes). The context process is expanded into five processes and three data stores, "
    "covering both backends:"
)
t = add_table([
    ["ID", "Process", "Input", "Output"],
    ["P1", "Manage account", "Credentials", "Session cookie / CSRF token"],
    ["P2", "Ingest document", "Uploaded file", "Extracted text (+ chunks/embeddings in rag_backend)"],
    ["P3", "Answer question", "Message / question, doc_ids", "Answer text, sources, citations"],
    ["P4", "Summarise & export", "Document id", "Executive summary, .docx report"],
    ["P5", "Search documents", "Query, format/doc filters", "Ranked, cross-format results"],
    ["Data store", "Content", "", ""],
    ["D1 SQLite", "Users, sessions, document metadata", "", ""],
    ["D2 ChromaDB", "Chunk text, metadata and embeddings (rag_backend only)", "", ""],
    ["D3 Media", "Uploaded files on local disk", "", ""],
], col_widths=[0.8, 1.6, 2.3, 2.2])
para("Table 5.2: DFD-1 processes and data stores", italic=True, size=9.5, color=GREY)
add_figure("fig_5_2_dfd1.png", "Figure 5.2: DFD level 1.")

para(
    "DFD-2 (detail of process P3). In rag_backend, \"Answer question\" is itself a small LangGraph workflow "
    "(chat/graph.py): P3.1 condense a follow-up question into a standalone one, P3.2 retrieve chunks with "
    "hybrid vector + BM25 + MMR scoring, P3.3 fit the retrieved chunks to the model's context budget, then a "
    "routing decision — if chunks were found, P3.4a asks Ollama to generate a grounded, cited answer; "
    "otherwise P3.4b returns a fixed not-found reply without ever calling the model."
)
add_figure("fig_5_3_dfd2.png",
           "Figure 5.3: DFD level 2 for process P3 (Answer question), traced directly to "
           "rag_backend/chat/graph.py's condense_node / retrieve_node / route / generate_node / "
           "not_found_node.")

h2("5.3 E-R Diagram")
para(
    "The system is mostly stream-oriented — most of what a conversation retrieves lives in ChromaDB, not a "
    "relational table — but it keeps a small set of persistent entities for users and documents. A finding "
    "worth stating plainly here, rather than smoothing into a single idealised schema: backend/ and "
    "rag_backend/ each define their own, incompatible Document model. The backend/ model has an owner "
    "foreign key and enforces per-user privacy; the rag_backend/ model has no owner field at all, so "
    "ownership is not yet enforced on that side. This is shown directly in the diagram rather than merged "
    "away."
)
t = add_table([
    ["Entity", "Main attributes"],
    ["User (Django auth)", "id (PK), username, is_staff"],
    ["Document (backend/)", "id (PK), owner_id (FK → User), original_name, file_type, extracted_text, "
     "uploaded_at"],
    ["Document (rag_backend/)", "id (PK), title, source_format, embedding_status, chunk_count, uploaded_at "
     "— no owner field"],
    ["Chunk (conceptual — lives in ChromaDB, not SQL)", "chunk_id = f\"{doc_id}__chunk{{i}}\" (PK), doc_id "
     "(FK), chunk_index, source, format, text, embedding vector"],
    ["ChatThread (conceptual — in-process only)", "thread_id (PK), doc_ids[] — held by LangGraph's "
     "MemorySaver; not persisted to any database and lost on restart"],
], col_widths=[2.3, 4.4])
para("Table 5.3: Entities and attributes", italic=True, size=9.5, color=GREY)
para(
    "Relationships. One User owns many Document (backend/) rows. One Document (rag_backend/) has many "
    "Chunk rows in ChromaDB. A ChatThread filters retrieval by a list of doc_ids but holds no foreign key to "
    "them — it is a query parameter, not a database relationship."
)
add_figure("fig_5_4_er.png",
           "Figure 5.4: E-R diagram. Dashed boxes mark entities that are not enforced or not persisted the "
           "way a conventional schema would be — the rag_backend Document table (no owner) and the "
           "in-memory ChatThread.")

h2("5.4 Class Diagram")
para(
    "The class design follows the module structure of the source code directly; class and method names "
    "below are copied from the repository rather than idealised."
)
t = add_table([
    ["Class", "Key attributes / methods", "Relationships"],
    ["ChatAPIView", "post()", "Calls ChatService.ask_ollama()"],
    ["DocumentUploadView", "post()", "Uses MultimodalExtractor / extractors"],
    ["DocumentAskView / DocumentSummaryView", "post()", "Uses ChatService (backend/) or the RAG path"],
    ["DocumentGenerateReportView", "post()", "Uses DocumentReportGenerator"],
    ["MultimodalExtractor", "extract_from_file(), is_supported()", "Used by DocumentUploadView and rag.py"],
    ["ChatService", "ask_ollama(message, thread_id, doc_ids)", "rag_backend version invokes RAGGraph; "
     "backend/ version calls Ollama directly on the whole document text"],
    ["RAGGraph", "condense_node(), retrieve_node(), route(), generate_node(), not_found_node()",
     "Calls SemanticSearch for retrieval"],
    ["SemanticSearch", "semantic_search(), group_by_format(), build_context_string()", "Reads from the "
     "Chroma vector store (rag.py: get_vectorstore)"],
    ["UnifiedSearchView", "get(), post()", "Calls retrieve_chunks() / SemanticSearch directly"],
    ["Document (model)", "owner (backend/ only), file, source_format, embedding_status, chunk_count",
     "Read/written by the views above"],
    ["DocumentReportGenerator", "generate_document_docx_report()", "Produces the .docx download"],
], col_widths=[1.9, 3.0, 1.8])
para("Table 5.4: Main classes", italic=True, size=9.5, color=GREY)
add_figure("fig_5_5_class.png",
           "Figure 5.5: Class diagram of the request path. The dashed arrows mark the RAG-specific path "
           "that only exists in rag_backend; the solid \"uses\" arrows exist in both backends.")

h2("5.5 Use Case Diagram")
para("Actors: Employee (end user), System Administrator, and Developer (the project's own maintainers).")
t = add_table([
    ["ID", "Use case", "Primary actor"],
    ["UC1", "Sign in", "Employee"],
    ["UC2", "Upload document (multi-format)", "Employee"],
    ["UC3", "Ask general question (Phase 1 chat)", "Employee"],
    ["UC4", "Ask document-grounded question", "Employee"],
    ["UC5", "Generate executive summary", "Employee"],
    ["UC6", "Export Word report", "Employee"],
    ["UC7", "Search across all documents (unified)", "Employee"],
    ["UC8", "Delete own document", "Employee"],
    ["UC9", "Create user account", "System Administrator"],
    ["UC10", "Run automated test suite", "Developer"],
    ["UC11", "Extend ingestion to a new file format", "Developer"],
], col_widths=[0.6, 3.9, 2.2])
para("Table 5.5: Use cases", italic=True, size=9.5, color=GREY)
para("UC2 includes retrieving/extracting text as part of upload; UC4 includes retrieving relevant chunks "
     "(rag_backend) before answering.")
add_figure("fig_5_6_usecase.png",
           "Figure 5.6: Use case diagram. Highlighted use cases (UC2, UC4) are the ones that include a "
           "further extraction/retrieval step.")

t = add_table([
    ["Use case", "Precondition", "Main flow", "Postcondition"],
    ["UC4 Ask document-grounded question", "User is signed in; at least one document is ingested",
     "1. Question reaches the API. 2. (rag_backend) The question is condensed, chunks are retrieved and "
     "fit to budget. 3. Ollama generates a cited answer, or the not-found reply is returned.",
     "Answer, sources and citations are returned to the dashboard."],
    ["UC6 Export Word report", "A document has been uploaded and (optionally) summarised",
     "1. User requests the report. 2. The API compiles metadata, summary and a text preview. 3. A .docx "
     "file is streamed back.", "User receives a downloadable Word file."],
    ["UC8 Delete own document", "User is signed in and owns the document (backend/)",
     "1. User requests deletion. 2. get_user_document() checks ownership (404 if not owner). 3. The "
     "database row and the physical file are removed.",
     "The document and its file no longer exist; other users' documents are unaffected."],
], col_widths=[1.3, 1.6, 3.1, 1.7])
para("Table 5.6: Selected use case descriptions", italic=True, size=9.5, color=GREY)

h2("5.6 Sequence Diagram")
para(
    "The sequence of messages for one document-grounded question, on the rag_backend path, is as follows "
    "(traced to rag_backend/chat/views.py, services.py and graph.py):"
)
add_bullets([
    "The Client types a question in the React SPA.",
    "The SPA sends POST /api/chat/ to ChatAPIView.",
    "ChatAPIView calls ChatService.ask_ollama(), which invokes the compiled LangGraph.",
    "The graph embeds the question and runs a similarity search against ChromaDB.",
    "ChromaDB returns the top-k candidate chunks.",
    "The graph builds a grounded, numbered-context prompt and calls Ollama's /api/generate.",
    "Ollama returns a completion, which is parsed into an answer plus citations.",
    "The graph returns {answer, sources, citations} to ChatAPIView, which returns JSON to the SPA.",
])
add_figure("fig_5_7_sequence.png",
           "Figure 5.7: Sequence diagram for one document-grounded question. Dashed arrows are returns.")
page_break()

# ═════════════════════════════════════════════════════════════════════════
# CHAPTER 6 — CONCLUSION & FUTURE SCOPE
# ═════════════════════════════════════════════════════════════════════════
h1("Chapter-6  Conclusion & Future Scope")
h2("6.1 Conclusion")
para(
    "The project delivers a working on-premise document-AI platform, not only a prompt wrapped around a "
    "local model. It authenticates users, extracts text from a wide range of file formats, and — in its "
    "newer rag_backend — chunks, embeds and retrieves that text with a hybrid vector/keyword/diversity "
    "ranking before ever asking the local LLM to answer, with numbered citations back to the source "
    "passages. A React dashboard, a Word-report exporter, a 200-function automated test suite, and a "
    "weekly auto-generated progress report round out a project that is closer to a small product than a "
    "single notebook demo."
)
para(
    "The main limitations, found directly while analysing the repository rather than assumed, are: (1) two "
    "independent Document schemas and permission models exist side by side — backend/ enforces per-user "
    "ownership, rag_backend/ does not yet; (2) a key-naming mismatch between semantic_search.py's chunk "
    "dictionaries (chunk_index, final_score) and two of its callers (graph.py, grading.py, which expect "
    "chunk and score) means the RAG chat path currently raises a KeyError on every call, caught by a broad "
    "except Exception in ChatAPIView and reported to the user as \"Local AI server is unavailable\" — "
    "masking the real defect as an Ollama outage; (3) the new offline test suite re-implements the scoring "
    "functions inline rather than importing them, so it cannot catch (2); and (4) a stray files (2)/ folder "
    "and two broken Git submodule links remain in the tree from earlier uploads. None of these are "
    "architectural flaws — they are exactly the kind of thing a requirements review and traceability table "
    "(Appendix A) is for."
)
h2("6.2 Future Scope")
add_bullets([
    "Fix the chunk-key mismatch in rag_backend/chat/graph.py and grading.py so the RAG chat path actually "
    "runs end to end, and narrow the broad except Exception in ChatAPIView so a real bug surfaces as an "
    "HTTP 500, not a misleading 503.",
    "Unify backend/ and rag_backend/ onto one Document schema and port the owner foreign key and per-user "
    "visibility checks across to the RAG side before any multi-user deployment.",
    "Make the offline unit tests import the real scoring functions from chat/semantic_search.py instead of "
    "duplicating them, so a regression in the real code actually fails a test.",
    "Add role-based access (plain employee vs. administrator) rather than relying only on Django's "
    "is_staff flag.",
    "Persist chat threads (currently held only in LangGraph's in-process MemorySaver) to a database so "
    "conversation history survives a server restart.",
    "Add a feedback mechanism so a user can flag a wrong or unhelpful answer, closing the loop that the "
    "guard/grading modules already partially support.",
    "Package the whole stack (Django, React build, Ollama) with Docker Compose for a one-command local "
    "deployment, and add a CI job that actually runs the 200-test suite on every push.",
    "Clean up repository hygiene: remove the duplicate files (2)/ folder and the two broken submodule "
    "gitlinks, and keep README section 5 (repository structure) in sync with the frontend's actual "
    "component tree.",
])
page_break()

# ═════════════════════════════════════════════════════════════════════════
# CHAPTER 7 — UN SDGs
# ═════════════════════════════════════════════════════════════════════════
h1("Chapter-7  UN Sustainable Development Goals")
h2("7. Mapping with UN Sustainable Development Goals")
para(
    "The 2030 Agenda for Sustainable Development was adopted by 193 Member States at the UN General "
    "Assembly in September 2015 and came into effect on 1 January 2016, setting 17 goals. This project maps "
    "mainly to SDG 9: Industry, Innovation and Infrastructure, because it builds self-hosted, resilient "
    "digital infrastructure that an organisation can run without depending on a third-party cloud AI "
    "vendor; and secondarily to SDG 16: Peace, Justice and Strong Institutions, because its privacy design "
    "(ALLOW_EXTERNAL_AI=False, localhost-only Ollama, per-user document isolation) is specifically about "
    "keeping an organisation's internal information inside its own institutional boundary."
)
t = add_table([
    ["S.No", "Product Objective", "Proposed Solution", "Mapping 3/2/1"],
    ["1", "Make document knowledge searchable without\nsending it to a third party", "On-premise Django + "
     "React stack with a local Ollama model", "3"],
    ["2", "Handle the formats organisations actually have", "Multi-format extractor (PDF, DOCX, XLSX, CSV, "
     "PPTX, image, audio)", "2"],
    ["3", "Give trustworthy, checkable answers rather than\nfluent guesses", "Hybrid retrieval + numbered "
     "citations + a fixed not-found reply when nothing matches", "2"],
    ["4", "Keep the system verifiably working as it grows", "200 automated test functions across both "
     "backends", "2"],
], col_widths=[0.5, 2.6, 2.6, 0.9])
para("SDG 9 — Industry, Innovation and Infrastructure", bold=True)
para("Table 7.1: Mapping to SDG 9", italic=True, size=9.5, color=GREY)

t = add_table([
    ["S.No", "Product Objective", "Proposed Solution", "Mapping 3/2/1"],
    ["1", "Keep internal documents and conversations\ninside the organisation", "ALLOW_EXTERNAL_AI=False, "
     "Ollama bound to 127.0.0.1, no public /media/ URL", "3"],
    ["2", "Limit a person's access to only what\nthey are entitled to see", "Per-user owner foreign key and "
     "ownership checks on every document endpoint (backend/)", "2"],
    ["3", "Protect credentials and sessions", "Session cookies are HttpOnly, SameSite=Lax; CSRF protection "
     "on write requests", "1"],
], col_widths=[0.5, 2.6, 2.6, 0.9])
para("SDG 16 — Peace, Justice and Strong Institutions", bold=True)
para("Table 7.2: Mapping to SDG 16", italic=True, size=9.5, color=GREY)
para(
    "The matrices represent the correlation of the product objective with the SDG. The correlation is "
    "defined on levels 1, 2 or 3: 1 = Slight (Low), 2 = Moderate (Medium), 3 = Substantial (High)."
)
page_break()

# ═════════════════════════════════════════════════════════════════════════
# APPENDIX A
# ═════════════════════════════════════════════════════════════════════════
h1("Appendix A: Requirement Traceability and Acceptance Checklist")
para(
    "Table A.1 links each requirement of Chapter 3 to the module that implements it and, where one already "
    "exists in the repository, to the test that verifies it. Table A.2 is a checklist to sign off during a "
    "final demonstration."
)
t = add_table([
    ["Requirement", "Design element (module or file)", "Verification"],
    ["FR-1.2", "chat/services.py: ask_ollama()", "backend/chat/tests.py: test_valid_message_success, "
     "test_ollama_server_connection_error"],
    ["FR-1.3", "documents/extractors.py", "backend/documents/tests.py: test_upload_valid_pdf_file, "
     "test_character_limit_truncation"],
    ["FR-1.4 / FR-1.5", "documents/services.py: ask_document_question, summarize_document",
     "backend/documents/tests.py: test_ask_question_about_document, test_summarize_document"],
    ["FR-1.6", "documents/generators.py", "backend/documents/tests.py: "
     "test_generate_and_download_docx_report"],
    ["FR-1.7", "documents/views.py: get_user_document()", "backend/documents/tests.py: "
     "DocumentOwnershipTests"],
    ["FR-2.1", "chat/multimodal_extractor.py", "rag_backend/chat/tests/test_extractor.py (41 tests)"],
    ["FR-2.2 / FR-2.3", "chat/rag.py: ingest_file, get_vectorstore", "rag_backend/chat/tests/"
     "test_retrieval_integration.py"],
    ["FR-2.4 / FR-2.5 / FR-2.6", "chat/semantic_search.py", "rag_backend/chat/tests/test_semantic_search.py "
     "(31 tests — currently against an inlined copy of the functions, see Section 6.1)"],
    ["FR-2.7", "chat/graph.py: condense_node", "rag_backend/chat/test_context.py, test_prompts.py"],
    ["FR-2.8", "chat/graph.py: route, not_found_node", "rag_backend/chat/test_grading.py"],
    ["FR-2.9", "chat/guards.py", "rag_backend/chat/test_guards.py"],
    ["FR-2.10", "documents/search_views.py: UnifiedSearchView", "rag_backend/documents/tests/"
     "test_search_api.py"],
    ["NFR-1", "settings.py: OLLAMA_KEEP_ALIVE, OLLAMA_THINK", "Manual measurement noted in the settings.py "
     "comment (10–60 s → 0.2–3 s)"],
    ["NFR-3", "chat/graph.py: retrieve_node try/except;\nchat/views.py: except Exception → 503",
     "backend/documents/tests.py: test_ollama_offline_returns_503"],
    ["NFR-4 / NFR-5", "accounts app; settings.py: ALLOW_EXTERNAL_AI, IsAuthenticated default",
     "backend/accounts/tests.py"],
    ["NFR-9", "Both test suites", "200 test functions measured 04/11/2026 (Figure 3.1)"],
], col_widths=[1.3, 2.6, 2.8])
para("Table A.1: Requirement traceability", italic=True, size=9.5, color=GREY)

h3("Table A.2: Acceptance checklist")
add_bullets([
    "A signed-in user can upload a PDF or TXT file and see its extracted text.",
    "A signed-in user cannot list, open or delete another user's document (backend/).",
    "A general chat message returns an Ollama-generated reply.",
    "A document-grounded question returns an answer drawn only from that document's text.",
    "An executive summary and a Word report can be generated and downloaded for a document.",
    "A multi-format file (e.g. an image or a spreadsheet) can be ingested and later found through unified "
    "search (rag_backend).",
    "Stopping Ollama causes chat/document endpoints to return HTTP 503, not a server crash.",
    "A greeting such as \"hi\" gets a direct reply without a retrieval pass.",
    "The RAG chat endpoint (POST /api/chat/, rag_backend) returns a normal JSON response instead of the "
    "KeyError described in Section 6.1 — this item is expected to fail until that fix is applied.",
    "The automated test suites for backend/ and rag_backend/ both pass.",
    "The weekly Form-3 report workflow runs successfully from the Actions tab.",
])

doc.save(OUT)
print("Document complete:", OUT)
