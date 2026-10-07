import React from 'react';
import { MessageSquare, FileText, ShieldCheck, LogIn, ArrowRight } from 'lucide-react';

const FEATURES = [
  {
    id: 'chat',
    icon: MessageSquare,
    title: 'General Chat',
    description: 'Ask questions and draft text with a local AI model running on the PC5 server.',
  },
  {
    id: 'documents',
    icon: FileText,
    title: 'Document Assistant',
    description: 'Upload PDF or TXT files, ask grounded questions, summarise and export Word reports.',
  },
  {
    id: 'privacy',
    icon: ShieldCheck,
    title: 'On-Premise & Private',
    description: 'No external cloud APIs. Prompts, documents and answers never leave the local network.',
  },
];

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

      <section className="home-features">
        {FEATURES.map(({ id, icon: Icon, title, description }) => {
          const isTool = user && id !== 'privacy';
          const content = (
            <>
              <div className="home-feature-icon">
                <Icon size={22} />
              </div>
              <h3 className="home-feature-title">{title}</h3>
              <p className="home-feature-desc">{description}</p>
              {isTool && (
                <span className="home-feature-link">
                  Open <ArrowRight size={14} />
                </span>
              )}
            </>
          );

          return isTool ? (
            <button key={id} type="button" className="home-feature-card clickable" onClick={() => onOpenTab(id)}>
              {content}
            </button>
          ) : (
            <div key={id} className="home-feature-card">
              {content}
            </div>
          );
        })}
      </section>
    </div>
  );
}
