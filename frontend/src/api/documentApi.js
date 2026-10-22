/**
 * documentApi.js  — Extended with the unified search endpoint.
 * Place in: frontend/src/api/documentApi.js
 */

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

// ─── Document management ────────────────────────────────────────────────────

export async function listDocuments() {
  const res = await fetch(`${BASE}/api/documents/`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function uploadDocument(file, onProgress) {
  const form = new FormData();
  form.append("file", file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE}/api/documents/`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total);
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        try {
          reject(new Error(JSON.parse(xhr.responseText).error ?? xhr.statusText));
        } catch {
          reject(new Error(xhr.statusText));
        }
      }
    };
    xhr.onerror = () => reject(new Error("Network error"));
    xhr.send(form);
  });
}

export async function deleteDocument(id) {
  const res = await fetch(`${BASE}/api/documents/${id}/`, { method: "DELETE" });
  if (!res.ok) throw new Error("Delete failed");
}

// ─── NEW: Unified cross-format semantic search ─────────────────────────────

/**
 * searchDocuments — semantic search across ALL indexed docs.
 *
 * @param {string}   query      Natural-language query
 * @param {object}   opts
 * @param {string[]} opts.formats  Filter by format labels, e.g. ["PDF","CSV"]
 * @param {string[]} opts.docIds   Filter by specific document IDs
 * @param {number}   opts.topK     Max results (default 10)
 *
 * @returns {Promise<{query, total, results: SearchResult[]}>}
 */
export async function searchDocuments(query, { formats = [], docIds = [], topK = 10 } = {}) {
  const params = new URLSearchParams({ q: query, top_k: topK });
  if (formats.length)  params.set("formats",  formats.join(","));
  if (docIds.length)   params.set("doc_ids",  docIds.join(","));

  const res = await fetch(`${BASE}/api/documents/search/?${params}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error ?? `Search failed (${res.status})`);
  }
  return res.json();
}
