import React from 'react';
import {
  MessageSquare,
  FileText,
  FileSearch,
  FileOutput,
  ScanText,
  ShieldCheck,
  ServerCog,
  Lock,
  LogIn,
  ArrowRight,
} from 'lucide-react';

// Tools the workbench offers. `tab` is the app tab a card opens; tools without
// one are shown as in development.
const CAPABILITIES = [
  {
    id: 'chatbot',
    tab: 'chat',
    icon: MessageSquare,
    title: 'AI Chatbot',
    description: 'Ask questions, explain concepts and draft emails or notes with the local AI model.',
  },
  {
    id: 'document-assistant',
    tab: 'documents',
    icon: FileSearch,
    title: 'Document Assistant',
    description: 'Upload PDF or TXT files and ask questions answered from the document content.',
  },
  {
    id: 'summaries',
    tab: 'documents',
    icon: FileText,
    title: 'Document Summaries',
    description: 'Get a concise summary of a long document in one click.',
  },
  {
    id: 'reports',
    tab: 'documents',
    icon: FileOutput,
    title: 'Word Report Export',
    description: 'Turn a document and its answers into a downloadable Word (.docx) report.',
  },
  {
    id: 'ocr',
    tab: null,
    icon: ScanText,
    title: 'OCR for Scanned Files',
    description: 'Extract text from images and scanned PDFs so they can be searched and questioned.',
  },
];

const HIGHLIGHTS = [
  {
    id: 'offline',
    icon: ServerCog,
    title: 'Runs on-premise',
    description: 'Served from the PC5 server over the local LAN.',
  },
  {
    id: 'private',
    icon: ShieldCheck,
    title: 'No external cloud APIs',
    description: 'Prompts, documents and answers stay on the local network.',
  },
  {
    id: 'secure',
    icon: Lock,
    title: 'Signed-in access',
    description: 'Only staff with administrator-issued accounts can use the tools.',
  },
];

function CapabilityCard({ capability, user, onOpenTab, onSignIn }) {
  const { icon: Icon, title, description, tab } = capability;
  const available = Boolean(tab);
  const handleClick = available ? (user ? () => onOpenTab(tab) : onSignIn) : null;

  const content = (
    <>
      <div className="home-feature-head">
        <div className="home-feature-icon">
          <Icon size={22} />
        </div>
        <span className={`home-feature-badge ${available ? 'available' : 'soon'}`}>
          {available ? 'Available' : 'In development'}
        </span>
      </div>
      <h3 className="home-feature-title">{title}</h3>
      <p className="home-feature-desc">{description}</p>
      {available && (
        <span className="home-feature-link">
          {user ? 'Open' : 'Sign in to use'} <ArrowRight size={14} />
        </span>
      )}
    </>
  );

  return handleClick ? (
    <button type="button" className="home-feature-card clickable" onClick={handleClick}>
      {content}
    </button>
  ) : (
    <div className="home-feature-card muted">{content}</div>
  );
}

/**
 * Landing page. Signed out: introduces the workbench and links to sign in.
 * Signed in: greets the user and opens the chosen tool.
 */
export default function HomePage({ user, onSignIn, onOpenTab }) {
  const displayName = user ? user.full_name || user.username : null;

  return (
    <div className="home-page">
      <section className="home-hero">
        <span className="home-eyebrow">MRPL AI Workbench</span>
        <h2 className="home-title">
          {displayName ? `Welcome back, ${displayName}` : 'Local AI for chat and documents'}
        </h2>
        <p className="home-lead">
          {displayName
            ? 'Pick a tool to get started. Everything runs on the on-premise PC5 server.'
            : 'A private AI assistant for MRPL staff, served from the PC5 server over the local LAN. Sign in with the credentials provided by your administrator.'}
        </p>
        {!user && (
          <button type="button" className="home-cta" onClick={onSignIn}>
            <LogIn size={18} />
            <span>Sign in</span>
          </button>
        )}
      </section>

      <section className="home-section">
        <h3 className="home-section-title">What you can do</h3>
        <div className="home-features">
          {CAPABILITIES.map((capability) => (
            <CapabilityCard
              key={capability.id}
              capability={capability}
              user={user}
              onOpenTab={onOpenTab}
              onSignIn={onSignIn}
            />
          ))}
        </div>
      </section>

      <section className="home-section">
        <h3 className="home-section-title">Private by design</h3>
        <div className="home-highlights">
          {HIGHLIGHTS.map(({ id, icon: Icon, title, description }) => (
            <div key={id} className="home-highlight">
              <Icon size={18} className="home-highlight-icon" />
              <div>
                <p className="home-highlight-title">{title}</p>
                <p className="home-highlight-desc">{description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
