import { useCallback, useEffect, useRef, useState } from 'react';
import { UploadCloud, FileText, Image as ImageIcon, Music, X, CheckCircle2, AlertCircle, RotateCw } from 'lucide-react';
import { uploadFile } from '../../api/uploadsApi';
import { ACCEPT, MODALITIES, extOf, modalityOf, prettySize } from '../../api/fileTypes';

const CONCURRENCY = 2;
const ICONS = { document: FileText, image: ImageIcon, audio: Music };
let nextId = 1;

export default function MultimodalUpload({ onUploaded }) {
  const [items, setItems] = useState([]); // {id,file,modality,status,progress,error,previewUrl}
  const [dragging, setDragging] = useState(false);
  const [running, setRunning] = useState(false);
  const inputRef = useRef(null);
  const itemsRef = useRef(items);
  itemsRef.current = items;

  // free object URLs when the component unmounts
  useEffect(() => () => itemsRef.current.forEach((i) => i.previewUrl && URL.revokeObjectURL(i.previewUrl)), []);

  const patch = (id, changes) => setItems((p) => p.map((i) => (i.id === id ? { ...i, ...changes } : i)));

  const addFiles = useCallback((fileList) => {
    const incoming = Array.from(fileList).map((file) => {
      const modality = modalityOf(file.name);
      let error = null;
      if (!modality) error = `${extOf(file.name) || 'This file'} is not a supported type`;
      else if (file.size === 0) error = 'File is empty';
      else if (file.size > MODALITIES[modality].maxMB * 1024 * 1024) error = `Larger than ${MODALITIES[modality].maxMB} MB`;
      const previewUrl = !error && (modality === 'image' || modality === 'audio') ? URL.createObjectURL(file) : null;
      return { id: nextId++, file, modality, status: error ? 'error' : 'queued', progress: 0, error, previewUrl, fatal: !!error };
    });
    setItems((prev) => {
      const seen = new Set(prev.map((p) => `${p.file.name}:${p.file.size}`));
      return [...prev, ...incoming.filter((i) => !seen.has(`${i.file.name}:${i.file.size}`))];
    });
  }, []);

  const runOne = async (item) => {
    patch(item.id, { status: 'uploading', progress: 0, error: null });
    try {
      const saved = await uploadFile(item.file, { onProgress: (p) => patch(item.id, { progress: p }) });
      patch(item.id, { status: 'done', progress: 100, note: saved?.note });
      onUploaded?.(saved);
    } catch (e) {
      patch(item.id, { status: 'error', error: e.message });
    }
  };

  const uploadAll = async () => {
    const queue = items.filter((i) => i.status === 'queued');
    if (!queue.length) return;
    setRunning(true);
    await Promise.all(Array.from({ length: Math.min(CONCURRENCY, queue.length) }, async () => {
      while (queue.length) await runOne(queue.shift());
    }));
    setRunning(false);
  };

  const remove = (id) => setItems((p) => {
    const gone = p.find((i) => i.id === id);
    if (gone?.previewUrl) URL.revokeObjectURL(gone.previewUrl);
    return p.filter((i) => i.id !== id);
  });
  const clearDone = () => items.filter((i) => i.status === 'done').forEach((i) => remove(i.id));

  const queued = items.filter((i) => i.status === 'queued').length;
  const done = items.filter((i) => i.status === 'done').length;

  return (
    <section className="mm">
      <div
        className={`mm-drop ${dragging ? 'is-dragging' : ''}`}
        role="button" tabIndex={0} aria-label="Choose files to upload"
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), inputRef.current?.click())}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }}
      >
        <UploadCloud size={30} aria-hidden="true" />
        <p className="mm-drop-title">Drop files here, or click to browse</p>
        <ul className="mm-types">
          {Object.entries(MODALITIES).map(([key, m]) => {
            const Icon = ICONS[key];
            return <li key={key} className={`t-${key}`}><Icon size={14} aria-hidden="true" /> {m.label}: {m.hint}</li>;
          })}
        </ul>
        <input ref={inputRef} type="file" multiple accept={ACCEPT} hidden
               onChange={(e) => { addFiles(e.target.files); e.target.value = ''; }} />
      </div>

      {items.length > 0 && (
        <>
          <ul className="mm-list">
            {items.map((it) => {
              const Icon = ICONS[it.modality] ?? FileText;
              return (
                <li key={it.id} className={`mm-row is-${it.status}`}>
                  <span className={`mm-thumb t-${it.modality}`}>
                    {it.modality === 'image' && it.previewUrl
                      ? <img src={it.previewUrl} alt="" />
                      : <Icon size={20} aria-hidden="true" />}
                  </span>
                  <div className="mm-meta">
                    <span className="mm-name" title={it.file.name}>{it.file.name}</span>
                    <span className="mm-sub">
                      {it.status === 'error' ? it.error
                        : it.status === 'done' ? 'Uploaded'
                        : it.status === 'uploading' ? `Uploading ${it.progress}%`
                        : prettySize(it.file.size)}
                    </span>
                    {it.status === 'uploading' && (
                      <div className="mm-bar" role="progressbar" aria-valuenow={it.progress} aria-valuemin={0} aria-valuemax={100}>
                        <div style={{ width: `${it.progress}%` }} />
                      </div>
                    )}
                    {it.modality === 'audio' && it.previewUrl && it.status === 'queued' && (
                      <audio controls preload="none" src={it.previewUrl} />
                    )}
                  </div>
                  {it.status === 'done' && <CheckCircle2 size={18} className="mm-ok" aria-label="Uploaded" />}
                  {it.status === 'error' && !it.fatal && (
                    <button type="button" className="mm-icon" aria-label={`Retry ${it.file.name}`}
                            onClick={() => patch(it.id, { status: 'queued', error: null, progress: 0 })}><RotateCw size={16} /></button>
                  )}
                  {it.status === 'error' && <AlertCircle size={18} className="mm-bad" aria-hidden="true" />}
                  {it.status !== 'uploading' && (
                    <button type="button" className="mm-icon" aria-label={`Remove ${it.file.name}`} onClick={() => remove(it.id)}><X size={16} /></button>
                  )}
                </li>
              );
            })}
          </ul>
          <div className="mm-actions">
            <button type="button" className="btn-primary" disabled={running || !queued} onClick={uploadAll}>
              {running ? 'Uploading…' : `Upload ${queued} file${queued === 1 ? '' : 's'}`}
            </button>
            {done > 0 && !running && <button type="button" className="btn-ghost" onClick={clearDone}>Clear uploaded</button>}
          </div>
        </>
      )}
    </section>
  );
}
