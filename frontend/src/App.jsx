import React, { useCallback, useEffect, useState } from 'react';
import Header from './components/Header';
import HomePage from './components/home/HomePage';
import LoginPage from './components/auth/LoginPage';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import DocumentsPage from './components/documents/DocumentsPage';
import { sendMessage } from './api/chatApi';
import { getCurrentUser, logout } from './api/authApi';

export default function App() {
  const [activeTab, setActiveTab] = useState('home'); // 'home' | 'chat' | 'documents'

  // Auth State: undefined while checking the session, null when signed out
  const [user, setUser] = useState(undefined);
  const [showLogin, setShowLogin] = useState(false);

  // Chat State
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const formatTime = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleSendMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    setError(null);
    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: text,
      time: formatTime(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const result = await sendMessage(text);

      if (result && result.success && result.response) {
        const botMsg = {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: result.response,
          time: formatTime(),
          model: result.model || 'local-ollama',
        };
        setMessages((prev) => [...prev, botMsg]);
      } else {
        const errorMsg = result?.error || "Unable to get response from local AI server.";
        setError(errorMsg);
      }
    } catch (err) {
      setError(err.message || "Failed to communicate with AI chat endpoint.");
    } finally {
      setIsLoading(false);
    }
  };

  const resetSession = useCallback(() => {
    setUser(null);
    setMessages([]);
    setError(null);
    setActiveTab('home');
  }, []);

  useEffect(() => {
    getCurrentUser().then((result) => setUser(result.authenticated ? result.user : null));
  }, []);

  // An API call came back 401/403: re-check the session and drop to the home page if it ended
  useEffect(() => {
    const handleExpired = async () => {
      const result = await getCurrentUser();
      if (!result.authenticated) resetSession();
    };
    window.addEventListener('auth:expired', handleExpired);
    return () => window.removeEventListener('auth:expired', handleExpired);
  }, [resetSession]);

  const handleLoginSuccess = (loggedInUser) => {
    setUser(loggedInUser);
    setShowLogin(false);
    setActiveTab('home');
  };

  const handleLogout = async () => {
    await logout();
    resetSession();
  };

  const handleSuggestionClick = (prompt) => {
    handleSendMessage(prompt);
  };

  if (user === undefined) {
    return (
      <div className="app-container">
        <div className="auth-loading">Checking session…</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="app-container">
        <Header user={null} onSignIn={showLogin ? null : () => setShowLogin(true)} />
        <main className="main-content">
          {showLogin ? (
            <LoginPage onLoginSuccess={handleLoginSuccess} onBack={() => setShowLogin(false)} />
          ) : (
            <HomePage user={null} onSignIn={() => setShowLogin(true)} />
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Header activeTab={activeTab} onTabChange={setActiveTab} user={user} onLogout={handleLogout} />

      <main className="main-content">
        {activeTab === 'home' ? (
          <HomePage user={user} onOpenTab={setActiveTab} />
        ) : activeTab === 'chat' ? (
          <div className="chat-layout">
            <ChatWindow
              messages={messages}
              isLoading={isLoading}
              error={error}
              onSuggestionClick={handleSuggestionClick}
            />
            <MessageInput
              onSendMessage={handleSendMessage}
              disabled={isLoading}
            />
          </div>
        ) : (
          <DocumentsPage />
        )}
      </main>
    </div>
  );
}
