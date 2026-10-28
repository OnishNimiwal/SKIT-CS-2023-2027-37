const BASE = '/api/uploads/'; // proxied to Django by vite.config.js

// Upload one file with progress (fetch() cannot report upload progress).
export function uploadFile(file, { onProgress } = {}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const form = new FormData();
    form.append('file', file);
    xhr.open('POST', BASE);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      let body = null;
      try { body = JSON.parse(xhr.responseText); } catch { /* not JSON */ }
      if (xhr.status >= 200 && xhr.status < 300) return resolve(body);
      reject(new Error(body?.error || body?.detail || `Upload failed (HTTP ${xhr.status})`));
    };
    xhr.onerror = () => reject(new Error('Cannot reach the server. Is the backend running?'));
    xhr.send(form);
  });
}

export async function listUploads(modality) {
  const res = await fetch(modality ? `${BASE}?modality=${modality}` : BASE);
  if (!res.ok) throw new Error(`Could not load uploads (HTTP ${res.status})`);
  const data = await res.json();
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function deleteUpload(id) {
  const res = await fetch(`${BASE}${id}/`, { method: 'DELETE' });
  if (!res.ok && res.status !== 204) throw new Error(`Could not delete (HTTP ${res.status})`);
}
