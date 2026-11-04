"""Real-data graphs for the MRPL AI Workbench SRS (Section 3.6 — Project Metrics).
All figures are drawn from values measured on the repository on 04/11/2026.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

OUT = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT, exist_ok=True)

BAR = "#2f6fdb"
BAR2 = "#7aa8f0"
TEXT = "#1a1a1a"
SUB = "#5f6368"
GRID = "#e6e6e0"

plt.rcParams.update({
    "font.size": 11,
    "axes.edgecolor": "#c9c9bd",
    "axes.labelcolor": TEXT,
    "text.color": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
})

def style_axes(ax):
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#c9c9bd")
    ax.set_axisbelow(True)

def save(fig, name, tight=True):
    if tight:
        fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=200, facecolor="white")
    plt.close(fig)
    print("saved", name)

def caption(ax, text):
    """Source caption pinned below the axes in axes-fraction coords (never collides with ticks)."""
    ax.text(0.0, -0.30, text, transform=ax.transAxes, fontsize=8, color=SUB, ha="left", va="top")


# ── Graph 3.1 — automated test functions by module ─────────────────────────
labels = ["rag_backend\n(Phase 3)", "backend\n(Phase 1/2)", "voice_search", "OCR_modul"]
values = [160, 34, 4, 2]
fig, ax = plt.subplots(figsize=(7.2, 4.3), dpi=200)
bars = ax.bar(labels, values, color=[BAR, BAR, BAR2, BAR2], width=0.55)
for b, v in zip(bars, values):
    ax.text(b.get_x() + b.get_width() / 2, v + 2.5, str(v), ha="center", fontsize=11, fontweight="bold")
ax.set_ylabel("test functions (def test_*)")
ax.set_title("Figure 3.1: Automated test functions by module", fontsize=12, fontweight="bold", loc="left")
ax.set_ylim(0, 180)
ax.grid(axis="y", color=GRID, linewidth=0.8)
style_axes(ax)
caption(ax, "Source: grep -rhoE \"def test_[a-zA-Z0-9_]*\" per module, counted 04/11/2026. Total: 200.")
save(fig, "graph_3_1_tests_by_module.png")

# ── Graph 3.2 — commits by contributor ──────────────────────────────────────
labels = ["Onish\nNimiwal", "Mohit\nPrasoya", "Priyanhu\nKhariwal", "github-actions\n[bot]", "Rajat\nYadav"]
values = [25, 22, 14, 9, 3]
colors = [BAR, BAR, BAR, "#b8b8ae", BAR]
fig, ax = plt.subplots(figsize=(7.2, 4.3), dpi=200)
bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1], height=0.55)
for b, v in zip(bars, values[::-1]):
    ax.text(v + 0.4, b.get_y() + b.get_height() / 2, str(v), va="center", fontsize=10.5, fontweight="bold")
ax.set_xlabel("commits (all branches)", labelpad=8)
ax.set_title("Figure 3.2: Commits by contributor", fontsize=12, fontweight="bold", loc="left")
ax.set_xlim(0, 30)
ax.grid(axis="x", color=GRID, linewidth=0.8)
style_axes(ax)
ax.text(0.0, -0.34, "Source: git shortlog -sn --all, 73 commits total, measured 04/11/2026.\n(bot = weekly Form-3 report automation)",
        transform=ax.transAxes, fontsize=8, color=SUB, ha="left", va="top")
fig.tight_layout()
fig.subplots_adjust(bottom=0.28)
save(fig, "graph_3_2_commits_by_contributor.png", tight=False)

# ── Graph 3.3 — tracked files per top-level directory ───────────────────────
labels = ["rag_backend", "frontend", "backend", "dashboard-\nuploads", "voice_search",
          "OCR_modul", "weekly_\nreports", "files (2)"]
values = [54, 38, 35, 21, 14, 11, 8, 11]
fig, ax = plt.subplots(figsize=(8.6, 4.3), dpi=200)
bars = ax.bar(labels, values, color=BAR, width=0.6)
for b, v in zip(bars, values):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.2, str(v), ha="center", fontsize=10, fontweight="bold")
ax.set_ylabel("tracked files")
ax.set_title("Figure 3.3: Tracked files per top-level directory", fontsize=12, fontweight="bold", loc="left")
ax.set_ylim(0, 62)
ax.grid(axis="y", color=GRID, linewidth=0.8)
style_axes(ax)
caption(ax, "Source: git ls-files, 203 tracked files total, measured 04/11/2026.")
save(fig, "graph_3_3_repo_composition.png")

# ── Graph 3.4 — cross-format taxonomy (exact colours from chat/semantic_search.py) ──
FORMAT_COLORS = {
    "PDF":               "#ef4444",
    "Word Document":     "#3b82f6",
    "Text":              "#64748b",
    "Markdown":          "#8b5cf6",
    "Excel Spreadsheet": "#22c55e",
    "CSV":               "#10b981",
    "TSV":               "#14b8a6",
    "PowerPoint":        "#f97316",
    "Image (OCR)":       "#f59e0b",
    "Audio Transcript":  "#6366f1",
    "Unknown":           "#94a3b8",
}
names = list(FORMAT_COLORS.keys())
colors = list(FORMAT_COLORS.values())
fig, ax = plt.subplots(figsize=(7.4, 5.2), dpi=200)
y = range(len(names))
ax.barh(list(y)[::-1], [1] * len(names), color=colors, height=0.65)
for i, (name, color) in enumerate(zip(names[::-1], colors[::-1])):
    ax.text(0.03, i, f"{name}   ({color})", va="center", ha="left", fontsize=10.5,
            color="white" if name not in ("Unknown",) else TEXT, fontweight="bold")
ax.set_xlim(0, 1)
ax.set_yticks([])
ax.set_xticks([])
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_title("Figure 3.4: Cross-format taxonomy and colour coding\n(chat/semantic_search.py: FORMAT_COLORS)",
             fontsize=12, fontweight="bold", loc="left")
save(fig, "graph_3_4_format_taxonomy.png")

print("All graphs generated.")
