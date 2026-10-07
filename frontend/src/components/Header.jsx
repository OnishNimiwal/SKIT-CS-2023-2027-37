import React from 'react';
import { ShieldCheck, Server, Cpu, Lock, MessageSquare, FileText, Home, LogIn, LogOut, UserCircle } from 'lucide-react';

export default function Header({ activeTab, onTabChange, user, onSignIn, onLogout }) {
  return (
    <header className="app-header">
      <div className="header-left">
        <div className="logo-badge">
          <Server className="logo-icon" size={22} />
        </div>
        <div>
          <h1 className="header-title">MRPL AI Workbench</h1>
          <p className="header-subtitle">Phase 2: Local AI Chat & Document Assistant</p>
        </div>
      </div>

      {/* Navigation Tabs (signed-in users only) */}
      {user && (
        <nav className="header-nav">
          <button
            className={`nav-tab-btn ${activeTab === 'home' ? 'active' : ''}`}
            onClick={() => onTabChange && onTabChange('home')}
          >
            <Home size={16} />
            <span>Home</span>
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => onTabChange && onTabChange('chat')}
          >
            <MessageSquare size={16} />
            <span>General Chat</span>
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => onTabChange && onTabChange('documents')}
          >
            <FileText size={16} />
            <span>Document Assistant</span>
            <span className="nav-tab-badge">Phase 2</span>
          </button>
        </nav>
      )}

      {/* Privacy & Compliance Badges */}
      <div className="header-badges">
        <div className="status-badge on-premise" title="Running strictly locally on PC5">
          <ShieldCheck size={14} className="badge-icon" />
          <span>Deployment: <strong>On-Premise</strong></span>
        </div>

        <div className="status-badge external-disabled" title="No external cloud APIs allowed">
          <Lock size={14} className="badge-icon" />
          <span>External API: <strong>Disabled</strong></span>
        </div>

        <div className="status-badge model-badge" title="Powered by local Ollama instance">
          <Cpu size={14} className="badge-icon" />
          <span>Model: <strong>Local Ollama</strong></span>
        </div>

        {user ? (
          <div className="header-user">
            <span className="header-user-name" title={`Signed in as ${user.username}`}>
              <UserCircle size={16} />
              <span>{user.full_name || user.username}</span>
            </span>
            <button type="button" className="header-auth-btn" onClick={onLogout}>
              <LogOut size={14} />
              <span>Logout</span>
            </button>
          </div>
        ) : (
          onSignIn && (
            <button type="button" className="header-auth-btn primary" onClick={onSignIn}>
              <LogIn size={14} />
              <span>Sign in</span>
            </button>
          )
        )}
      </div>
    </header>
  );
}
