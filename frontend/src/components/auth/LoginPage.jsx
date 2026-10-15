import React, { useState } from 'react';
import { Lock, User, Eye, EyeOff, LogIn, ArrowLeft, AlertCircle } from 'lucide-react';
import { login } from '../../api/authApi';

export default function LoginPage({ onLoginSuccess, onBack }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password || isSubmitting) return;

    setError(null);
    setIsSubmitting(true);
    const result = await login(username.trim(), password);
    setIsSubmitting(false);

    if (result.success) {
      setPassword('');
      onLoginSuccess(result.user);
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit} noValidate>
        <div className="login-card-header">
          <div className="logo-badge">
            <Lock size={20} />
          </div>
          <div>
            <h2 className="login-title">Sign in</h2>
            <p className="login-subtitle">Use the account created by your workbench administrator.</p>
          </div>
        </div>

        {error && (
          <div className="login-error" role="alert">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <label className="login-label" htmlFor="login-username">Username</label>
        <div className="login-input-wrap">
          <User size={16} className="login-input-icon" />
          <input
            id="login-username"
            className="login-input"
            type="text"
            autoComplete="username"
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <label className="login-label" htmlFor="login-password">Password</label>
        <div className="login-input-wrap">
          <Lock size={16} className="login-input-icon" />
          <input
            id="login-password"
            className="login-input"
            type={showPassword ? 'text' : 'password'}
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isSubmitting}
          />
          <button
            type="button"
            className="login-toggle"
            onClick={() => setShowPassword((v) => !v)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>

        <button
          type="submit"
          className="login-submit"
          disabled={!username.trim() || !password || isSubmitting}
        >
          <LogIn size={16} />
          <span>{isSubmitting ? 'Signing in…' : 'Sign in'}</span>
        </button>

        <button type="button" className="login-back" onClick={onBack}>
          <ArrowLeft size={14} />
          <span>Back to home</span>
        </button>
      </form>
    </div>
  );
}
