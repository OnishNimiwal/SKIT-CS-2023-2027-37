"""Generate all diagrams/figures for the MRPL AI Workbench SRS.

Every diagram reserves an explicit header band for its (possibly 2-line) title
before any box is placed, and every box's bounding box is computed and checked
against the canvas edges and the header band before saving, so nothing can
silently clip or collide the way the first two drafts did.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
from matplotlib.lines import Line2D
import os

OUT = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT, exist_ok=True)

BORDER = "#b9b9ac"
BLUE_BORDER = "#2f6fdb"
BLUE_FILL = "#dbe8fd"
TEXT = "#141414"
SUBTEXT = "#52565b"
BG = "#ffffff"
DIAMOND_FILL = "#fff3d6"

TITLE_FS = 15
BOX_TITLE_FS = 12
BOX_SUB_FS = 10.5
LABEL_FS = 9.8

plt.rcParams["font.family"] = "DejaVu Sans"

_boxes = []  # collected per-figure for the overlap check


def new_fig(w, h, title):
    """title: list of 1-2 lines. Returns (fig, ax, content_top) — content_top is
    the highest y a box's TOP EDGE may use without touching the title."""
    global _boxes
    _boxes = []
    lines = title if isinstance(title, list) else [title]
    fig, ax = plt.subplots(figsize=(w, h), dpi=220)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    y = h - 0.45
    for line in lines:
        ax.text(0.3, y, line, fontsize=TITLE_FS, fontweight="bold", color=TEXT, ha="left", va="top")
        y -= 0.52
    content_top = y - 0.25  # clearance below the last title line
    return fig, ax, content_top


def box(ax, cx, cy, w, h, title, sub=None, highlight=False, dashed=False,
        title_fs=BOX_TITLE_FS, sub_fs=BOX_SUB_FS):
    fc = BLUE_FILL if highlight else "#ffffff"
    ec = BLUE_BORDER if highlight else BORDER
    lw = 2.2 if highlight else 1.4
    patch = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                            boxstyle="round,pad=0.02,rounding_size=0.11",
                            linewidth=lw, edgecolor=ec, facecolor=fc,
                            linestyle="--" if dashed else "-", zorder=2)
    ax.add_patch(patch)
    if sub:
        title_lines, sub_lines = title.split("\n"), sub.split("\n")
        total = len(title_lines) + len(sub_lines) + 0.6
        line_h = h / (total + 0.5)
        y = cy + h / 2 - line_h * 0.95
        for line in title_lines:
            ax.text(cx, y, line, ha="center", va="center", fontsize=title_fs, fontweight="bold",
                    color=TEXT, zorder=3)
            y -= line_h
        y -= line_h * 0.5
        for line in sub_lines:
            ax.text(cx, y, line, ha="center", va="center", fontsize=sub_fs, color=SUBTEXT, zorder=3)
            y -= line_h
    else:
        lines = title.split("\n")
        line_h = min(h / (len(lines) + 0.9), 0.46)
        y = cy + (len(lines) - 1) * line_h / 2
        for line in lines:
            ax.text(cx, y, line, ha="center", va="center", fontsize=title_fs, fontweight="bold",
                    color=TEXT, zorder=3)
            y -= line_h
    bbox = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    _boxes.append(bbox)
    return bbox


def diamond(ax, cx, cy, w, h, title, fontsize=10.5):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, edgecolor=BORDER, facecolor=DIAMOND_FILL, linewidth=1.4, zorder=2))
    lines = title.split("\n")
    line_h = 0.32
    y = cy + (len(lines) - 1) * line_h / 2
    for line in lines:
        ax.text(cx, y, line, ha="center", va="center", fontsize=fontsize, fontweight="bold",
                color=TEXT, zorder=3)
        y -= line_h
    _boxes.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))


def arrow(ax, p1, p2, dashed=False, rad=0.0, lw=1.6):
    a = FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=13, color="#8a8a7e",
                         linewidth=lw, linestyle="--" if dashed else "-",
                         connectionstyle=f"arc3,rad={rad}", shrinkA=3, shrinkB=3, zorder=1)
    ax.add_patch(a)


def label(ax, x, y, text, ha="center", va="center", fontsize=LABEL_FS, color=TEXT):
    ax.text(x, y, text, ha=ha, va=va, fontsize=fontsize, color=color, zorder=5,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.94))


def check(w, h, content_top, margin=0.25):
    """Print a warning for any box that clips the canvas or the title band —
    run before save() so problems are caught, not shipped."""
    ok = True
    for (x0, y0, x1, y1) in _boxes:
        if x0 < margin or x1 > w - margin or y0 < margin:
            print(f"  !! box out of canvas bounds: ({x0:.2f},{y0:.2f})-({x1:.2f},{y1:.2f}) canvas w={w} h={h}")
            ok = False
        if y1 > content_top + 0.02:
            print(f"  !! box crosses into title band: top={y1:.2f} > content_top={content_top:.2f}")
            ok = False
    return ok


def save(fig, name, w=None, h=None, content_top=None):
    if w is not None:
        check(w, h, content_top)
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", pad_inches=0.15, facecolor=BG)
    plt.close(fig)
    print("saved", name)


# ═════════════════════════════════════════════════════════════════════════
# Figure 4.0 — Context diagram
# ═════════════════════════════════════════════════════════════════════════
W, H = 11.4, 8.2
fig, ax, ctop = new_fig(W, H, ["The Workbench sits between LAN users", "and the local Ollama engine"])
cy_top = ctop - 1.05  # top boxes' centre, leaving 1.05 half-height + label clearance below ctop
box(ax, 1.9, cy_top, 2.6, 1.5, "Employee", "Browser on\nPC2 / PC3 / PC4")
box(ax, 5.8, cy_top, 3.2, 1.7, "MRPL AI Workbench", "Django REST API +\nReact SPA (PC5)", highlight=True)
box(ax, 9.7, cy_top, 2.6, 1.5, "Ollama Engine", "qwen3:4b +\nnomic-embed-text")
cy_bot = cy_top - 3.3
box(ax, 5.8, cy_bot, 3.2, 1.3, "Administrator", "signed-in\ndocument owner")

arrow(ax, (3.2, cy_top + 0.35), (4.2, cy_top + 0.35))
label(ax, 3.7, cy_top + 0.9, "HTTP request\n(chat/upload/ask)", fontsize=9)
arrow(ax, (4.2, cy_top - 0.35), (3.2, cy_top - 0.35))
label(ax, 3.7, cy_top - 0.9, "JSON answer /\n.docx report", fontsize=9)

arrow(ax, (7.4, cy_top + 0.35), (8.4, cy_top + 0.35))
label(ax, 7.9, cy_top + 0.8, "prompt / embed", fontsize=9)
arrow(ax, (8.4, cy_top - 0.35), (7.4, cy_top - 0.35))
label(ax, 7.9, cy_top - 0.8, "completion / vectors", fontsize=9)

arrow(ax, (5.3, cy_bot + 0.65), (5.3, cy_top - 0.85))
label(ax, 4.25, (cy_bot + cy_top) / 2, "login, upload,\nfeedback", fontsize=9)
arrow(ax, (6.3, cy_top - 0.85), (6.3, cy_bot + 0.65))
label(ax, 7.45, (cy_bot + cy_top) / 2, "answers, summaries,\nreports", fontsize=9)
save(fig, "fig_4_0_context.png", W, H, ctop)

# ═════════════════════════════════════════════════════════════════════════
# Figure 4.1 — Client-server / layered architecture
# ═════════════════════════════════════════════════════════════════════════
W, H = 12.4, 7.6
fig, ax, ctop = new_fig(W, H, "Client-Server Architecture")
top = ctop - 0.9
box(ax, 1.5, top, 2.2, 1.3, "Browser", ":5173 (LAN)")
box(ax, 4.3, top, 2.6, 1.3, "React SPA", "Chat, Documents,\nDashboard")
box(ax, 7.6, top, 3.0, 1.5, "Django REST API", ":8000\nchat / documents / rag", highlight=True)
box(ax, 10.9, top, 2.2, 1.3, "Ollama", ":11434")

bot = top - 2.9
box(ax, 2.0, bot, 2.4, 1.4, "SQLite", "db.sqlite3\nusers, documents")
box(ax, 4.9, bot, 2.4, 1.4, "Media storage", "documents/\non disk")
box(ax, 7.8, bot, 2.4, 1.4, "ChromaDB", "vector_db/\n(rag_backend only)")
box(ax, 10.7, bot, 2.2, 1.4, "qwen3:4b /\nnomic-embed", None)

arrow(ax, (2.6, top), (3.0, top))
label(ax, 2.8, top + 0.42, "HTTP", fontsize=8.6)
arrow(ax, (5.6, top), (6.1, top))
label(ax, 5.85, top + 0.42, "fetch()/api/*", fontsize=8.6)
arrow(ax, (9.1, top), (9.8, top))
label(ax, 9.45, top + 0.42, "/api/generate", fontsize=8.6)

arrow(ax, (7.0, top - 0.75), (2.1, bot + 0.7), rad=-0.12)
arrow(ax, (7.4, top - 0.75), (4.9, bot + 0.7), rad=-0.08)
arrow(ax, (7.8, top - 0.75), (7.8, bot + 0.7))
arrow(ax, (8.4, top - 0.75), (10.5, bot + 0.7), rad=0.12)

ax.text(0.9, bot - 1.3, "Phase 1 / 2  (backend/)", fontsize=10, color=SUBTEXT, style="italic", ha="left")
ax.text(6.6, bot - 1.3, "Phase 3  (rag_backend/)", fontsize=10, color=SUBTEXT, style="italic", ha="left")
save(fig, "fig_4_1_client_server.png", W, H, ctop)

# ═════════════════════════════════════════════════════════════════════════
# Figure 5.1 — DFD level 0
# ═════════════════════════════════════════════════════════════════════════
W, H = 11.2, 5.4
fig, ax, ctop = new_fig(W, H, "DFD level 0 — 1 process, 2 external entities")
cy = ctop - 1.35
box(ax, 1.8, cy, 2.6, 1.6, "Employee / User", "sends requests")
box(ax, 5.6, cy, 3.1, 1.8, "MRPL AI Workbench", "chat, documents, RAG", highlight=True)
box(ax, 9.3, cy, 2.4, 1.6, "System Admin", "createsuperuser\n/admin/")

arrow(ax, (3.1, cy + 0.5), (4.05, cy + 0.5))
label(ax, 3.55, cy + 1.1, "message / file / question", fontsize=8.6)
arrow(ax, (4.05, cy - 0.5), (3.1, cy - 0.5))
label(ax, 3.55, cy - 1.1, "answer / summary / report", fontsize=8.6)

arrow(ax, (8.1, cy + 0.5), (7.15, cy + 0.5))
label(ax, 7.6, cy + 1.1, "account created", fontsize=8.6)
arrow(ax, (7.15, cy - 0.5), (8.1, cy - 0.5))
label(ax, 7.6, cy - 1.1, "manages via\nDjango admin", fontsize=8.6)
save(fig, "fig_5_1_dfd0.png", W, H, ctop)

# ═════════════════════════════════════════════════════════════════════════
# Figure 5.2 — DFD level 1
# ═════════════════════════════════════════════════════════════════════════
W, H = 14.3, 9.6
fig, ax, ctop = new_fig(W, H, "DFD level 1 — 5 processes, 3 data stores")
r1 = ctop - 0.75
r2 = r1 - 2.3
r3 = r2 - 2.3
box(ax, 1.4, r2 - 0.5, 2.1, 1.1, "E1 User", None, title_fs=11)
box(ax, 1.4, r3 + 0.0, 2.1, 1.1, "E2 Admin", None, title_fs=11)

box(ax, 5.1, r1, 2.6, 1.2, "P1 Manage\naccount", "login/logout")
box(ax, 5.1, r2, 2.8, 1.3, "P2 Ingest\ndocument", "upload + extract")
box(ax, 8.9, r2, 3.0, 1.5, "P3 Answer\nquestion", "chat / doc Q&A / RAG", highlight=True)
box(ax, 12.3, r1, 2.3, 1.3, "P4 Summarise\n& export", None)
box(ax, 12.3, r2 + 0.3, 2.3, 1.3, "P5 Search\ndocuments", None)

box(ax, 5.1, r3, 2.4, 1.2, "D1 SQLite", "users, documents")
box(ax, 8.9, r3, 2.4, 1.2, "D2 ChromaDB", "chunks + vectors")
box(ax, 12.3, r3 - 0.8, 2.3, 1.2, "D3 Media", "uploaded files")

arrow(ax, (2.45, r2 - 0.15), (3.8, r1 + 0.1), rad=0.1)
label(ax, 3.1, r1 + 0.5, "credentials", fontsize=8.6)
arrow(ax, (2.45, r3 + 0.15), (3.8, r3 + 0.0))
label(ax, 3.1, r3 + 0.45, "account mgmt", fontsize=8.6)
arrow(ax, (1.4, r2 - 1.05), (1.4, r3 + 0.55), rad=0.35)
arrow(ax, (2.45, r2 - 0.1), (3.7, r2))

arrow(ax, (6.45, r2), (7.4, r2))
label(ax, 6.9, r2 + 0.38, "text", fontsize=8.6)
arrow(ax, (5.1, r2 - 0.65), (5.1, r3 + 0.6))
label(ax, 5.65, (r2 + r3) / 2, "stores", fontsize=8.6)
arrow(ax, (5.85, r2 - 0.65), (8.2, r3 + 0.6), rad=-0.12)
label(ax, 6.9, r2 - 0.85, "embeds", fontsize=8.6)
arrow(ax, (8.9, r2 - 0.75), (8.9, r3 + 0.6))
label(ax, 9.45, (r2 + r3) / 2, "reads\nchunks", fontsize=8.6)

arrow(ax, (10.3, r2 + 0.5), (11.15, r1), rad=-0.12)
label(ax, 10.85, r1 + 0.55, "summary", fontsize=8.6)
arrow(ax, (10.4, r2 - 0.2), (11.15, r2 + 0.1), rad=0.1)
label(ax, 10.85, r2 - 0.5, "answer", fontsize=8.6)
arrow(ax, (12.3, r1 - 0.65), (12.3, r2 + 0.95))
label(ax, 12.95, (r1 + r2) / 2, "doc text", fontsize=8.6)
arrow(ax, (12.3, r1 - 0.65), (12.3, r3 - 0.2), rad=0.3)
save(fig, "fig_5_2_dfd1.png", W, H, ctop)

# ═════════════════════════════════════════════════════════════════════════
# Figure 5.3 — DFD level 2, detail of P3
# ═════════════════════════════════════════════════════════════════════════
W, H = 14.8, 7.2
fig, ax, ctop = new_fig(W, H, ["DFD level 2 — detail of process P3", "(Answer question, rag_backend/chat/graph.py)"])
cy = ctop - 2.15
box(ax, 1.5, cy, 2.4, 1.3, "P3.1 Condense\nfollow-up", "condense_node")
box(ax, 4.5, cy, 2.6, 1.3, "P3.2 Retrieve\nchunks", "vector + BM25\n+ MMR")
box(ax, 7.6, cy, 2.4, 1.3, "P3.3 Fit to\ncontext budget", "fit_chunks_\nto_budget")
diamond(ax, 10.4, cy, 2.0, 1.7, "chunks\nfound?")
box(ax, 13.3, cy + 1.4, 2.2, 1.3, "P3.4a Generate\nanswer", "Ollama +\ncitations", highlight=True)
box(ax, 13.3, cy - 1.4, 2.2, 1.3, "P3.4b Not-found\nreply", None)

arrow(ax, (2.7, cy), (3.2, cy))
label(ax, 2.95, cy + 0.42, "question", fontsize=8.6)
arrow(ax, (5.8, cy), (6.4, cy))
label(ax, 6.1, cy + 0.42, "top-k chunks", fontsize=8.6)
arrow(ax, (8.8, cy), (9.4, cy))
label(ax, 9.1, cy + 0.42, "chunks", fontsize=8.6)
arrow(ax, (11.25, cy + 0.55), (12.2, cy + 1.1), rad=0.1)
label(ax, 11.75, cy + 0.6, "yes", fontsize=9.3)
arrow(ax, (11.25, cy - 0.55), (12.2, cy - 1.1), rad=-0.1)
label(ax, 11.75, cy - 0.6, "no", fontsize=9.3)
save(fig, "fig_5_3_dfd2.png", W, H, ctop)

# ═════════════════════════════════════════════════════════════════════════
# Figure 5.4 — ER diagram
# ═════════════════════════════════════════════════════════════════════════
W, H = 13.4, 9.6
fig, ax, ctop = new_fig(W, H, ["Entity-Relationship diagram (current schema)", "note the two independent Document tables"])
r1 = ctop - 1.0
r2 = r1 - 3.2
box(ax, 1.9, r1, 2.7, 1.5, "User", "id (PK), username,\nis_staff")
box(ax, 5.9, r1, 3.6, 1.9, "Document (backend/)", "id (PK), owner_id (FK),\noriginal_name, file_type,\nextracted_text, uploaded_at", highlight=True)
box(ax, 10.4, r1, 3.7, 1.9, "Document (rag_backend/)",
    "id (PK), title, source_format,\nembedding_status, chunk_count\n— no owner FK", dashed=True)
box(ax, 10.4, r2, 3.7, 1.9, "Chunk",
    "chunk_id (PK), doc_id (FK),\nchunk_index, format, text,\nembedding (in ChromaDB)")
box(ax, 5.9, r2, 3.5, 1.7, "ChatThread",
    "thread_id (PK), doc_ids[]\n— in-process memory only,\nnot persisted (MemorySaver)", dashed=True)

arrow(ax, (3.25, r1), (4.1, r1))
label(ax, 3.55, r1 + 0.42, "1  owns  N", fontsize=9)
arrow(ax, (10.4, r1 - 0.95), (10.4, r2 + 0.95))
label(ax, 11.0, (r1 + r2) / 2, "1  has  N", fontsize=9)
arrow(ax, (7.65, r2), (8.55, r2), dashed=True)
label(ax, 8.1, r2 + 0.42, "filters by\ndoc_ids", fontsize=8.6)
save(fig, "fig_5_4_er.png", W, H, ctop)

# ═════════════════════════════════════════════════════════════════════════
# Figure 5.5 — Class diagram
# ═════════════════════════════════════════════════════════════════════════
W, H = 15.6, 11.0
fig, ax, ctop = new_fig(W, H, "Class diagram of the request path")
col1, col2, col3 = 2.3, 6.9, 12.0
r1 = ctop - 0.95
r2 = r1 - 2.0
r3 = r2 - 2.3
r4 = r3 - 2.1

box(ax, col1, r1, 3.5, 1.2, "ChatAPIView", "post()")
box(ax, col1, r2, 3.7, 1.4, "DocumentUploadView", "post()")
box(ax, col1, r3, 3.7, 1.7, "DocumentAskView /\nDocumentSummaryView", "post()")
box(ax, col1, r4, 3.9, 1.4, "DocumentGenerateReportView", "post()")

box(ax, col2, r2, 3.7, 1.7, "MultimodalExtractor", "extract_from_file(),\nis_supported()")
box(ax, col2, r3, 3.7, 1.7, "ChatService", "ask_ollama(message,\nthread_id, doc_ids)", highlight=True)
box(ax, col2, r4, 3.7, 1.7, "DocumentReportGenerator", "generate_document_\ndocx_report()")

box(ax, col3, r1, 3.3, 1.7, "RAGGraph", "condense_node(),\nretrieve_node(),\ngenerate_node()")
box(ax, col3, r2, 3.3, 1.8, "SemanticSearch", "semantic_search(),\ngroup_by_format(),\nbuild_context_string()")
box(ax, col3, r3, 3.3, 1.4, "UnifiedSearchView", "get(), post()")
box(ax, col3, r4, 3.3, 1.5, "Document (model)", "owner, file,\nsource_format")

arrow(ax, (4.15, r2), (5.05, r2))
label(ax, 4.6, r2 + 0.42, "uses", fontsize=8.6)
arrow(ax, (4.15, r3), (5.05, r3))
label(ax, 4.6, r3 + 0.52, "uses", fontsize=8.6)
arrow(ax, (4.25, r4), (5.05, r4))
label(ax, 4.65, r4 + 0.42, "uses", fontsize=8.6)

arrow(ax, (8.75, r3 - 0.4), (10.35, r2 + 0.55), rad=-0.15)
label(ax, 9.75, r3 - 0.55, "RAG path\ninvokes", fontsize=8.6)
arrow(ax, (10.5, r1 - 0.8), (8.75, r3 + 0.1), rad=0.18, dashed=True)
label(ax, 10.4, (r1 + r3) / 2 + 0.3, "falls through\nto", fontsize=8.4)
arrow(ax, (col3, r1 - 0.85), (col3, r2 + 0.9))
label(ax, col3 + 1.0, (r1 + r2) / 2, "calls", fontsize=8.6)
arrow(ax, (10.35, r3 - 0.1), (8.75, r3 + 0.45))
label(ax, 9.75, r3 + 0.55, "calls", fontsize=8.6)
arrow(ax, (col3, r4 + 0.75), (col3, r3 - 0.7), dashed=True)
label(ax, col3 + 1.1, (r3 + r4) / 2, "reads/\nwrites", fontsize=8.4)
save(fig, "fig_5_5_class.png", W, H, ctop)

# ═════════════════════════════════════════════════════════════════════════
# Figure 5.6 — Use case diagram
# ═════════════════════════════════════════════════════════════════════════
W, H = 13.0, 11.7
fig, ax, ctop = new_fig(W, H, "Use case diagram")
actor_x, uc1_x, uc2_x = 1.3, 5.6, 9.7
r1 = ctop - 0.75
r2 = r1 - 1.5
r3 = r2 - 1.5
r4 = r3 - 1.5
r5 = r4 - 1.9

employee_y = (r1 + r3) / 2
box(ax, actor_x, employee_y, 2.0, 1.1, "Employee", None, title_fs=11)
box(ax, actor_x, r4, 2.0, 1.3, "System\nAdministrator", None, title_fs=10.5)
r6 = r5 - 2.0
box(ax, actor_x, r6, 2.0, 1.1, "Developer", None, title_fs=11)

uc_w, uc_h = 3.4, 1.25
box(ax, uc1_x, r1, uc_w, uc_h, "UC1 Sign in", None, title_fs=10)
box(ax, uc1_x, r2, uc_w, uc_h, "UC2 Upload document\n(multi-format)", None, highlight=True, title_fs=10)
box(ax, uc1_x, r3, uc_w, uc_h, "UC3 Ask general\nquestion (Phase 1)", None, title_fs=10)
box(ax, uc1_x, r4, uc_w, uc_h, "UC4 Ask document-\ngrounded question", None, highlight=True, title_fs=10)
box(ax, uc1_x, r5, uc_w, uc_h, "UC8 Delete own\ndocument", None, title_fs=10)

box(ax, uc2_x, r1, uc_w, uc_h, "UC5 Generate executive\nsummary", None, title_fs=10)
box(ax, uc2_x, r2, uc_w, uc_h, "UC6 Export Word report", None, title_fs=10)
box(ax, uc2_x, r3, uc_w, uc_h, "UC7 Search across all\ndocuments (unified)", None, title_fs=10)
box(ax, uc2_x, r4, uc_w, uc_h, "UC9 Create user\naccount", None, title_fs=10)

box(ax, uc1_x, r6, uc_w, uc_h, "UC10 Run automated\ntest suite", None, title_fs=10)
box(ax, uc2_x, r6, uc_w, uc_h, "UC11 Extend ingestion to\na new file format", None, title_fs=10)

arrow(ax, (2.3, employee_y + 0.35), (3.9, r1), rad=0.1)
arrow(ax, (2.3, employee_y + 0.1), (3.9, r2), rad=0.05)
arrow(ax, (2.3, employee_y - 0.15), (3.9, r3))
arrow(ax, (2.3, employee_y - 0.4), (3.9, r4), rad=-0.12)
arrow(ax, (2.3, employee_y - 0.5), (3.9, r5), rad=-0.18)
arrow(ax, (2.3, r4 + 0.35), (3.9, r2 - 0.3), rad=0.22)
arrow(ax, (2.3, r4), (7.95, r4 - 0.3), rad=-0.15)
arrow(ax, (2.3, r6), (3.9, r6))
arrow(ax, (2.3, r6 + 0.1), (7.95, r6), rad=-0.1)

arrow(ax, (7.3, r2), (7.95, r2), dashed=True)
label(ax, 7.6, r2 + 0.42, "include", fontsize=8.6)
arrow(ax, (7.3, r4), (7.95, r4), dashed=True)
label(ax, 7.6, r4 + 0.42, "include", fontsize=8.6)
save(fig, "fig_5_6_usecase.png", W, H, ctop)

# ═════════════════════════════════════════════════════════════════════════
# Figure 5.7 — Sequence diagram
# ═════════════════════════════════════════════════════════════════════════
W, H = 15.5, 8.8
fig, ax, ctop = new_fig(W, H, ["The dashboard waits for the graph's decision", "before showing an answer"])
lanes = [("Client", 1.6), ("React SPA", 4.4), ("ChatAPIView", 7.5),
         ("LangGraph\n(condense/retrieve/\ngenerate)", 10.8), ("ChromaDB /\nOllama", 13.9)]
top = ctop - 0.85
for name, x in lanes:
    box(ax, x, top, 2.6, 1.5, name, None, highlight=(name == "ChatAPIView"), title_fs=11)
    ax.add_line(Line2D([x, x], [0.5, top - 0.8], color=BORDER, linestyle="--", linewidth=1.2, zorder=0))

steps = [
    (1.6, 4.4, "1  types question", top - 1.35, False),
    (4.4, 7.5, "2  POST /api/chat/", top - 1.95, False),
    (7.5, 10.8, "3  invoke(graph)", top - 2.55, False),
    (10.8, 13.9, "4  embed + similarity_search", top - 3.15, False),
    (13.9, 10.8, "5  top-k chunks", top - 3.75, True),
    (10.8, 13.9, "6  /api/generate (grounded prompt)", top - 4.35, False),
    (13.9, 10.8, "7  completion + citations", top - 4.95, True),
    (10.8, 7.5, "8  answer, sources, citations", top - 5.55, True),
    (7.5, 4.4, "9  JSON response", top - 6.15, True),
]
for x1, x2, text, y, dashed in steps:
    arrow(ax, (x1, y), (x2, y), dashed=dashed)
    label(ax, (x1 + x2) / 2, y + 0.3, text, fontsize=9.3)
save(fig, "fig_5_7_sequence.png", W, H, ctop)

print("All diagrams generated.")
