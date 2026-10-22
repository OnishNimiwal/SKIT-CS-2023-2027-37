/**
 * UnifiedSearch.jsx — Full cross-format semantic search panel
 * 
 * Features:
 *  • Live search with debounce
 *  • Format filter sidebar (PDF, DOCX, XLSX, CSV, PPTX, Image OCR, Audio)
 *  • Colour-coded format badges per result
 *  • Relevance score bar
 *  • Highlighted matched text
 *  • Responsive dark-themed design
 *
 * Place in: frontend/src/components/UnifiedSearch.jsx
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { searchDocuments } from "../api/documentApi";

// ─── Constants ────────────────────────────────────────────────────────────────

const ALL_FORMATS = [
  { label: "PDF",               color: "#ef4444", icon: "📄" },
  { label: "Word Document",     color: "#3b82f6", icon: "📝" },
  { label: "Excel Spreadsheet", color: "#22c55e", icon: "📊" },
  { label: "CSV",               color: "#10b981", icon: "📋" },
  { label: "PowerPoint",        color: "#f97316", icon: "📑" },
  { label: "Image (OCR)",       color: "#f59e0b", icon: "🖼️" },
  { label: "Audio Transcript",  color: "#6366f1", icon: "🎙️" },
  { label: "Text",              color: "#64748b", icon: "📃" },
  { label: "Markdown",          color: "#8b5cf6", icon: "📜" },
];

const FORMAT_MAP = Object.fromEntries(ALL_FORMATS.map((f) => [f.label, f]));


// ─── Utility: highlight query words in text ──────────────────────────────────

function HighlightedText({ text, query }) {
  if (!query.trim()) return <span>{text}</span>;
  const words = query
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const re = new RegExp(`(${words.join("|")})`, "gi");
  const parts = text.split(re);
  return (
    <span>
      {parts.map((p, i) =>
        re.test(p) ? (
          <mark key={i} style={{ background: "#fde047", color: "#1e293b", borderRadius: 3, padding: "0 2px" }}>
            {p}
          </mark>
        ) : (
          <span key={i}>{p}</span>
        )
      )}
    </span>
  );
}


// ─── Format Badge ────────────────────────────────────────────────────────────

function FormatBadge({ format, color }) {
  const meta = FORMAT_MAP[format] || { icon: "📁", color: color || "#94a3b8" };
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "2px 10px",
        borderRadius: 20,
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.04em",
        background: meta.color + "22",
        color: meta.color,
        border: `1px solid ${meta.color}44`,
        whiteSpace: "nowrap",
      }}
    >
      {meta.icon} {format}
    </span>
  );
}


// ─── Score Bar ───────────────────────────────────────────────────────────────

function ScoreBar({ score }) {
  const pct = Math.round(score * 100);
  const color = score > 0.7 ? "#22c55e" : score > 0.45 ? "#f59e0b" : "#ef4444";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div
        style={{
          flex: 1,
          height: 4,
          borderRadius: 2,
          background: "#1e293b",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            borderRadius: 2,
            background: color,
            transition: "width 0.5s ease",
          }}
        />
      </div>
      <span style={{ fontSize: 11, color, fontWeight: 600, minWidth: 36 }}>
        {pct}%
      </span>
    </div>
  );
}


// ─── Result Card ─────────────────────────────────────────────────────────────

function ResultCard({ result, query, index }) {
  const [expanded, setExpanded] = useState(false);
  const TEXT_LIMIT = 220;
  const long = result.text.length > TEXT_LIMIT;

  return (
    <div
      className="result-card"
      style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        border: "1px solid #334155",
        borderRadius: 14,
        padding: "18px 22px",
        display: "flex",
        flexDirection: "column",
        gap: 12,
        animation: `slideUp 0.3s ease ${index * 0.05}s both`,
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 10, flexWrap: "wrap" }}>
        <FormatBadge format={result.format} color={result.format_color} />
        <span
          style={{
            fontSize: 12,
            color: "#94a3b8",
            marginLeft: "auto",
            fontFamily: "monospace",
          }}
        >
          {result.source} · chunk #{result.chunk_index}
        </span>
      </div>

      {/* Score */}
      <ScoreBar score={result.score} />

      {/* Text */}
      <p
        style={{
          margin: 0,
          fontSize: 14,
          lineHeight: 1.7,
          color: "#cbd5e1",
        }}
      >
        <HighlightedText
          text={expanded || !long ? result.text : result.text.slice(0, TEXT_LIMIT) + "…"}
          query={query}
        />
      </p>

      {long && (
        <button
          onClick={() => setExpanded((x) => !x)}
          style={{
            background: "none",
            border: "none",
            color: "#818cf8",
            cursor: "pointer",
            fontSize: 12,
            padding: 0,
            textAlign: "left",
          }}
        >
          {expanded ? "▲ Show less" : "▼ Show more"}
        </button>
      )}
    </div>
  );
}


// ─── Format Filter Pill ──────────────────────────────────────────────────────

function FormatPill({ meta, active, toggle }) {
  return (
    <button
      onClick={toggle}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        padding: "5px 13px",
        borderRadius: 20,
        fontSize: 12,
        fontWeight: 600,
        cursor: "pointer",
        transition: "all 0.15s",
        background: active ? meta.color + "33" : "transparent",
        color: active ? meta.color : "#64748b",
        border: `1.5px solid ${active ? meta.color : "#334155"}`,
      }}
    >
      {meta.icon} {meta.label}
    </button>
  );
}


// ─── Main Component ──────────────────────────────────────────────────────────

export default function UnifiedSearch() {
  const [query, setQuery]           = useState("");
  const [activeFormats, setActive]  = useState(new Set());
  const [results, setResults]       = useState(null);  // null = not searched yet
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState("");
  const [topK, setTopK]             = useState(10);
  const debounceRef                 = useRef(null);
  const inputRef                    = useRef(null);

  const doSearch = useCallback(async (q, formats, k) => {
    if (!q.trim()) { setResults(null); return; }
    setLoading(true);
    setError("");
    try {
      const data = await searchDocuments(q, {
        formats: [...formats],
        topK: k,
      });
      setResults(data);
    } catch (e) {
      setError(e.message);
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounced search on input change
  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(
      () => doSearch(query, activeFormats, topK),
      520
    );
    return () => clearTimeout(debounceRef.current);
  }, [query, activeFormats, topK, doSearch]);

  const toggleFormat = (label) =>
    setActive((prev) => {
      const next = new Set(prev);
      next.has(label) ? next.delete(label) : next.add(label);
      return next;
    });

  const clearAll = () => {
    setQuery("");
    setActive(new Set());
    setResults(null);
    setError("");
    inputRef.current?.focus();
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%)",
        fontFamily: "'Inter', 'Segoe UI', sans-serif",
        color: "#f1f5f9",
        padding: "0 0 60px",
      }}
    >
      {/* ─── Header ──────────────────────────────────────────────────── */}
      <header
        style={{
          background: "rgba(15,23,42,0.85)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid #1e293b",
          padding: "20px 40px",
          display: "flex",
          alignItems: "center",
          gap: 14,
          position: "sticky",
          top: 0,
          zIndex: 100,
        }}
      >
        <span style={{ fontSize: 28 }}>🔍</span>
        <div>
          <h1
            style={{
              margin: 0,
              fontSize: 20,
              fontWeight: 800,
              background: "linear-gradient(90deg, #818cf8, #38bdf8)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              letterSpacing: "-0.02em",
            }}
          >
            Multimodal Semantic Search
          </h1>
          <p style={{ margin: 0, fontSize: 12, color: "#64748b" }}>
            Search across PDF · DOCX · XLSX · CSV · PPTX · Images · Audio — all at once
          </p>
        </div>

        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          <span
            style={{
              fontSize: 11,
              padding: "3px 10px",
              borderRadius: 20,
              background: "#22c55e22",
              color: "#22c55e",
              border: "1px solid #22c55e44",
              fontWeight: 600,
            }}
          >
            🟢 ChromaDB Connected
          </span>
          <span
            style={{
              fontSize: 11,
              padding: "3px 10px",
              borderRadius: 20,
              background: "#818cf822",
              color: "#818cf8",
              border: "1px solid #818cf844",
              fontWeight: 600,
            }}
          >
            ⚡ OllamaEmbeddings
          </span>
        </div>
      </header>

      {/* ─── Search Bar ──────────────────────────────────────────────── */}
      <div style={{ maxWidth: 860, margin: "40px auto 0", padding: "0 20px" }}>
        <div
          style={{
            position: "relative",
            background: "rgba(30,41,59,0.8)",
            border: "1.5px solid #334155",
            borderRadius: 16,
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "14px 20px",
            boxShadow: "0 4px 32px rgba(99,102,241,0.15)",
            transition: "border-color 0.2s",
          }}
          onFocus={() => {}} // handled by input itself
        >
          <span style={{ fontSize: 20, flexShrink: 0 }}>🔎</span>
          <input
            ref={inputRef}
            id="unified-search-input"
            type="text"
            placeholder="Search across all documents… (e.g. 'quarterly revenue targets')"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              flex: 1,
              background: "none",
              border: "none",
              outline: "none",
              fontSize: 16,
              color: "#f1f5f9",
              fontFamily: "inherit",
            }}
            aria-label="Search documents"
          />
          {(query || activeFormats.size > 0) && (
            <button
              onClick={clearAll}
              style={{
                background: "#334155",
                border: "none",
                borderRadius: 8,
                color: "#94a3b8",
                cursor: "pointer",
                padding: "4px 10px",
                fontSize: 12,
              }}
            >
              ✕ Clear
            </button>
          )}
        </div>

        {/* ─── Format Filters ────────────────────────────────────────── */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
            marginTop: 16,
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: 12, color: "#64748b", marginRight: 4 }}>
            Filter by format:
          </span>
          {ALL_FORMATS.map((meta) => (
            <FormatPill
              key={meta.label}
              meta={meta}
              active={activeFormats.has(meta.label)}
              toggle={() => toggleFormat(meta.label)}
            />
          ))}

          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
            <label style={{ fontSize: 12, color: "#64748b" }}>Max results:</label>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              style={{
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: 8,
                color: "#f1f5f9",
                padding: "4px 8px",
                fontSize: 12,
              }}
            >
              {[5, 10, 20, 30].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* ─── Results ─────────────────────────────────────────────────── */}
      <div style={{ maxWidth: 860, margin: "28px auto 0", padding: "0 20px" }}>

        {/* Loading state */}
        {loading && (
          <div style={{ textAlign: "center", padding: 60 }}>
            <div
              style={{
                display: "inline-block",
                width: 40,
                height: 40,
                border: "3px solid #334155",
                borderTopColor: "#818cf8",
                borderRadius: "50%",
                animation: "spin 0.8s linear infinite",
              }}
            />
            <p style={{ color: "#64748b", marginTop: 16, fontSize: 14 }}>
              Searching vector database…
            </p>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div
            style={{
              background: "#ef444422",
              border: "1px solid #ef444444",
              borderRadius: 12,
              padding: 20,
              color: "#fca5a5",
              fontSize: 14,
            }}
          >
            ⚠️ {error}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && results === null && !query && (
          <div style={{ textAlign: "center", padding: "60px 20px" }}>
            <div style={{ fontSize: 64, marginBottom: 20 }}>🗂️</div>
            <h2 style={{ color: "#64748b", fontWeight: 600, fontSize: 18 }}>
              Search across all your documents
            </h2>
            <p style={{ color: "#475569", fontSize: 14, maxWidth: 400, margin: "0 auto" }}>
              Type any natural-language query above. Results are ranked by semantic
              similarity and may come from PDFs, spreadsheets, slides, images, or audio.
            </p>
          </div>
        )}

        {/* No results */}
        {!loading && !error && results !== null && results.total === 0 && (
          <div style={{ textAlign: "center", padding: "40px 20px" }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>🔍</div>
            <p style={{ color: "#64748b", fontSize: 14 }}>
              No results found for <strong style={{ color: "#f1f5f9" }}>"{results.query}"</strong>
              {activeFormats.size > 0 && ` in selected formats`}.
            </p>
          </div>
        )}

        {/* Results header */}
        {!loading && results && results.total > 0 && (
          <>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 16,
              }}
            >
              <p style={{ margin: 0, color: "#94a3b8", fontSize: 13 }}>
                <strong style={{ color: "#f1f5f9" }}>{results.total}</strong> results for{" "}
                <strong style={{ color: "#818cf8" }}>"{results.query}"</strong>
              </p>
              {/* Format distribution pills */}
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {[...new Set(results.results.map((r) => r.format))].map((fmt) => {
                  const count = results.results.filter((r) => r.format === fmt).length;
                  const meta  = FORMAT_MAP[fmt] || { icon: "📁", color: "#94a3b8" };
                  return (
                    <span
                      key={fmt}
                      style={{
                        fontSize: 11,
                        padding: "2px 8px",
                        borderRadius: 20,
                        background: meta.color + "22",
                        color: meta.color,
                        border: `1px solid ${meta.color}44`,
                      }}
                    >
                      {meta.icon} {fmt} ({count})
                    </span>
                  );
                })}
              </div>
            </div>

            {/* Result cards */}
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {results.results.map((result, i) => (
                <ResultCard key={`${result.doc_id}-${result.chunk_index}`} result={result} query={results.query} index={i} />
              ))}
            </div>
          </>
        )}
      </div>

      {/* ─── Animations ──────────────────────────────────────────────── */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .result-card:hover {
          border-color: #818cf844 !important;
          box-shadow: 0 0 0 1px #818cf822, 0 8px 32px rgba(99,102,241,0.12);
          transform: translateY(-1px);
          transition: all 0.2s ease;
        }

        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
      `}</style>
    </div>
  );
}
