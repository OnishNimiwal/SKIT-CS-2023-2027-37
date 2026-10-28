import { useEffect, useState } from 'react';
import { LayoutDashboard, MessageSquare, FileText, UploadCloud, ShieldCheck, Menu, X } from 'lucide-react';
import useHashRoute from '../../hooks/useHashRoute';
import '../../dashboard.css';

// Add a page = add one line here + one entry in the `routes` prop.
export const NAV = [
  { id: 'overview',  label: 'Overview',      icon: LayoutDashboard },
  { id: 'chat',      label: 'AI Chat',       icon: MessageSquare },
  { id: 'documents', label: 'Document Q&A',  icon: FileText },
  { id: 'uploads',   label: 'Upload Center', icon: UploadCloud },
];

/**
 * routes: { overview: <Element/>, chat: <Element/>, documents: <Element/>, uploads: <Element/> }
 */
export default function DashboardLayout({ routes }) {
  const route = useHashRoute('overview');
  const [open, setOpen] = useState(false);
  const active = NAV.find((n) => n.id === route) ?? NAV[0];

  useEffect(() => { setOpen(false); document.title = `${active.label} · MRPL AI Workbench`; }, [active]);

  return (
    <div className="db-shell">
      <aside className={`db-sidebar ${open ? 'is-open' : ''}`} aria-label="Main navigation">
        <div className="db-brand">
          <span className="db-brand-mark" aria-hidden="true">M</span>
          <div><strong>MRPL AI Workbench</strong><small>Internal · On-premise</small></div>
          <button type="button" className="db-close" onClick={() => setOpen(false)} aria-label="Close menu"><X size={18} /></button>
        </div>
        <nav>
          {NAV.map(({ id, label, icon: Icon }) => (
            <a key={id} href={`#/${id}`} className={`db-link ${id === active.id ? 'is-active' : ''}`}
               aria-current={id === active.id ? 'page' : undefined}>
              <Icon size={18} aria-hidden="true" /> {label}
            </a>
          ))}
        </nav>
        <div className="db-privacy"><ShieldCheck size={16} aria-hidden="true" /> Runs fully offline on this server</div>
      </aside>
      {open && <div className="db-scrim" onClick={() => setOpen(false)} />}

      <div className="db-main">
        <header className="db-header">
          <button type="button" className="db-burger" onClick={() => setOpen(true)} aria-label="Open menu"><Menu size={20} /></button>
          <h1>{active.label}</h1>
          <ul className="db-badges">
            <li>Deployment: On-Premise</li>
            <li>External API: Disabled</li>
            <li>Model: Local Ollama (Qwen)</li>
          </ul>
        </header>
        <main className="db-content">{routes[active.id] ?? routes.overview}</main>
      </div>
    </div>
  );
}
