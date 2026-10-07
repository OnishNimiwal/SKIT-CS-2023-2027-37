import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import { Bot, AlertTriangle, Sparkles } from 'lucide-react';

export default function ChatWindow({ messages, isLoading, error, onSuggestionClick }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, error]);

  const suggestions = [
    "Explain how on-premise AI models protect sensitive corporate data.",
    "Write a Python function to parse JSON logs efficiently.",
    "Draft an internal announcement about the new MRPL AI Workbench.",
    "How does Ollama run local LLMs on an internal workstation?",
  ];

  return (
    <div className="chat-window">
      {messages.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon-wrap">
            <Bot size={40} className="empty-bot-icon" />
          </div>
          <h2>Welcome to MRPL AI Workbench</h2>
          <p className="empty-desc">
            Your local AI assistant powered by Ollama and Qwen on PC5.
            Zero external cloud data transfer, completely secure within your LAN.
          </p>

          <div className="suggestions-grid">
            {suggestions.map((item, idx) => (
              <button
                key={idx}
                className="suggestion-card"
                onClick={() => onSuggestionClick && onSuggestionClick(item)}
              >
                <Sparkles size={14} className="suggestion-icon" />
                <span>{item}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="messages-list">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {isLoading && (
            <div className="message-row bot-row">
              <div className="avatar bot-avatar">
                <Bot size={18} />
              </div>
              <div className="message-content-wrapper">
                <div className="message-meta">
                  <span className="sender-name">MRPL Local AI</span>
                  <span className="message-time">Generating...</span>
                </div>
                <div className="message-bubble bot-bubble loading-bubble">
                  <div className="typing-indicator">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                  <span className="loading-text">Processing locally on PC5...</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="error-banner">
              <AlertTriangle size={18} className="error-icon" />
              <div className="error-text">
                <strong>Service Notice:</strong> {error}
                <div className="error-hint">
                  If the Ollama model is downloading, please wait a moment and try again.
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
