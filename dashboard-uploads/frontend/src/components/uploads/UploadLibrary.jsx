import { useCallback, useEffect, useState } from 'react';
import { FileText, Image as ImageIcon, Music, Trash2 } from 'lucide-react';
import { deleteUpload, listUploads } from '../../api/uploadsApi';
import { MODALITIES, prettySize } from '../../api/fileTypes';

const ICONS = { document: FileText, image: ImageIcon, audio: Music };
const STATUS = { processed: 'Text extracted', stored: 'Stored', failed: 'Failed' };

export default function UploadLibrary({ refreshKey = 0 }) {
  const [filter, setFilter] = useState('all');
  const [rows, setRows] = useState(null); // null = loading
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try { setError(null); setRows(await listUploads(filter === 'all' ? undefined : filter)); }
    catch (e) { setError(e.message); setRows([]); }
  }, [filter]);

  useEffect(() => { load(); }, [load, refreshKey]);

  const remove = async (row) => {
    if (!window.confirm(`Delete "${row.original_name}"? This also removes the file from the server.`)) return;
    try { await deleteUpload(row.id); setRows((r) => r.filter((x) => x.id !== row.id)); }
    catch (e) { setError(e.message); }
  };

  return (
    <section className="lib">
      <div className="lib-head">
        <h2>Uploaded files</h2>
        <div className="lib-filters" role="group" aria-label="Filter by type">
          {['all', ...Object.keys(MODALITIES)].map((k) => (
            <button key={k} type="button" className={filter === k ? 'is-on' : ''} aria-pressed={filter === k} onClick={() => setFilter(k)}>
              {k === 'all' ? 'All' : MODALITIES[k].label}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="lib-error" role="alert">{error}</p>}
      {rows === null && <p className="lib-empty">Loading…</p>}
      {rows?.length === 0 && !error && <p className="lib-empty">Nothing here yet. Upload a file to see it listed.</p>}

      <ul className="lib-list">
        {rows?.map((r) => {
          const Icon = ICONS[r.modality] ?? FileText;
          return (
            <li key={r.id} className="lib-row">
              <span className={`mm-thumb t-${r.modality}`}><Icon size={18} aria-hidden="true" /></span>
              <div className="lib-meta">
                <span className="mm-name" title={r.original_name}>{r.original_name}</span>
                <span className="mm-sub">
                  {MODALITIES[r.modality]?.label.replace(/s$/, '')} · {prettySize(r.size)} · {new Date(r.created_at).toLocaleString()}
                </span>
                {r.note && <span className="mm-sub">{r.note}</span>}
                {r.text_preview && (
                  <details>
                    <summary>Preview extracted text ({r.char_count.toLocaleString()} characters)</summary>
                    <pre>{r.text_preview}{r.char_count > r.text_preview.length ? '\n…' : ''}</pre>
                  </details>
                )}
              </div>
              <span className={`pill s-${r.status}`}>{STATUS[r.status] ?? r.status}</span>
              <button type="button" className="mm-icon" aria-label={`Delete ${r.original_name}`} onClick={() => remove(r)}><Trash2 size={16} /></button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
