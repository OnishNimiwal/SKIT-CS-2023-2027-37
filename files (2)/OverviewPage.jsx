import { useEffect, useState } from 'react';
import { FileText, Image as ImageIcon, Music, UploadCloud, MessageSquare } from 'lucide-react';
import { listUploads } from '../api/uploadsApi';
import { MODALITIES, prettySize } from '../api/fileTypes';

const ICONS = { document: FileText, image: ImageIcon, audio: Music };

export default function OverviewPage() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => { listUploads().then(setRows).catch((e) => { setError(e.message); setRows([]); }); }, []);

  const count = (m) => rows?.filter((r) => r.modality === m).length ?? '–';
  const bytes = rows?.reduce((s, r) => s + r.size, 0) ?? 0;

  return (
    <div className="stack">
      {error && <p className="lib-error" role="alert">{error}</p>}

      <div className="stats">
        {Object.entries(MODALITIES).map(([k, m]) => {
          const Icon = ICONS[k];
          return (
            <a key={k} href="#/uploads" className={`stat t-${k}`}>
              <Icon size={20} aria-hidden="true" />
              <strong>{count(k)}</strong>
              <span>{m.label}</span>
            </a>
          );
        })}
        <div className="stat"><strong>{rows ? prettySize(bytes) : '–'}</strong><span>Stored on server</span></div>
      </div>

      <div className="grid-2">
        <section className="card">
          <h2>Quick actions</h2>
          <div className="actions">
            <a className="btn-primary" href="#/uploads"><UploadCloud size={16} /> Upload files</a>
            <a className="btn-ghost" href="#/chat"><MessageSquare size={16} /> Open AI chat</a>
            <a className="btn-ghost" href="#/documents"><FileText size={16} /> Ask a document</a>
          </div>
        </section>

        <section className="card">
          <h2>Recent uploads</h2>
          {rows === null && <p className="lib-empty">Loading…</p>}
          {rows?.length === 0 && <p className="lib-empty">No uploads yet.</p>}
          <ul className="recent">
            {rows?.slice(0, 5).map((r) => (
              <li key={r.id}><span className="mm-name">{r.original_name}</span><span className="mm-sub">{new Date(r.created_at).toLocaleDateString()}</span></li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
