/** Auth API: session login / logout against the Django backend. */

import { apiFetch } from './http';

const API_BASE = import.meta.env.VITE_API_URL || '';

/** Returns { authenticated, user }. Also sets the CSRF cookie needed for later writes. */
export async function getCurrentUser() {
  try {
    const response = await apiFetch(`${API_BASE}/api/auth/me/`, { skipAuthEvent: true });
    if (!response.ok) return { authenticated: false, user: null };
    return await response.json();
  } catch {
    return { authenticated: false, user: null, error: 'Unable to reach the workbench server.' };
  }
}

export async function login(username, password) {
  try {
    // Make sure the CSRF cookie exists before the first POST
    await apiFetch(`${API_BASE}/api/auth/csrf/`, { skipAuthEvent: true });
    const response = await apiFetch(`${API_BASE}/api/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
      skipAuthEvent: true,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      return { success: false, error: data.error || `Sign-in failed (${response.status}).` };
    }
    return data;
  } catch {
    return { success: false, error: 'Unable to reach the workbench server.' };
  }
}

export async function logout() {
  try {
    await apiFetch(`${API_BASE}/api/auth/logout/`, { method: 'POST', skipAuthEvent: true });
  } catch {
    // Ignore network errors: the UI returns to the login screen either way
  }
  return { success: true };
}
