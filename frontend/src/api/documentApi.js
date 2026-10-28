/**
 * API client for MRPL AI Workbench - Document Assistant
 * Handles document upload, listing, details, Q&A, summarization, docx export, and deletion.
 */

import { apiFetch } from './http';

const API_BASE = import.meta.env.VITE_API_URL || '';

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await apiFetch(`${API_BASE}/api/documents/upload/`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      return {
        success: false,
        error: data.error || (data.errors ? JSON.stringify(data.errors) : 'Upload failed'),
        status: response.status,
      };
    }
    return data;
  } catch (err) {
    return {
      success: false,
      error: 'Network error communicating with server during upload.',
      details: err.message,
    };
  }
}

export async function getDocuments() {
  try {
    const response = await apiFetch(`${API_BASE}/api/documents/`);
    const data = await response.json();
    if (!response.ok) {
      return { success: false, error: data.error || 'Failed to fetch documents' };
    }
    return data;
  } catch (err) {
    return { success: false, error: err.message };
  }
}

export async function getDocument(id) {
  try {
    const response = await apiFetch(`${API_BASE}/api/documents/${id}/`);
    const data = await response.json();
    if (!response.ok) {
      return { success: false, error: data.error || 'Failed to fetch document details' };
    }
    return data;
  } catch (err) {
    return { success: false, error: err.message };
  }
}

export async function askDocument(id, question) {
  try {
    const response = await apiFetch(`${API_BASE}/api/documents/${id}/ask/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    const data = await response.json();
    if (!response.ok) {
      return {
        success: false,
        error: data.error || 'Failed to get answer from local AI',
        status: response.status,
      };
    }
    return data;
  } catch (err) {
    return { success: false, error: err.message };
  }
}

export async function summarizeDocument(id) {
  try {
    const response = await apiFetch(`${API_BASE}/api/documents/${id}/summary/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    const data = await response.json();
    if (!response.ok) {
      return {
        success: false,
        error: data.error || 'Failed to generate summary from local AI',
        status: response.status,
      };
    }
    return data;
  } catch (err) {
    return { success: false, error: err.message };
  }
}

export async function downloadDocumentReport(id, summaryText = '', defaultFilename = 'report.docx') {
  try {
    const response = await apiFetch(`${API_BASE}/api/documents/${id}/generate-report/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ summary: summaryText }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      return {
        success: false,
        error: errData.error || `Failed to generate report (${response.status})`,
      };
    }

    // Extract filename from header if present
    const disposition = response.headers.get('Content-Disposition');
    let filename = defaultFilename;
    if (disposition && disposition.includes('filename=')) {
      const matches = disposition.match(/filename="?([^";]+)"?/);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);

    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

export async function deleteDocument(id) {
  try {
    const response = await apiFetch(`${API_BASE}/api/documents/${id}/`, {
      method: 'DELETE',
    });

    const data = await response.json();
    if (!response.ok) {
      return { success: false, error: data.error || 'Failed to delete document' };
    }
    return data;
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// ─── Unified multimodal search (rag_backend) ────────────────────────────────
// Used by components/UnifiedSearch.jsx. Talks to the rag_backend search endpoint,
// which is a separate server from the main app's /api.
const SEARCH_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

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

  const res = await fetch(`${SEARCH_BASE}/api/documents/search/?${params}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error ?? `Search failed (${res.status})`);
  }
  return res.json();
}
