/**
 * Shared fetch wrapper for the Django backend.
 * Sends the session cookie and, on write requests, the CSRF token Django expects.
 * Fires an "auth:expired" window event on 401/403 so the app can return to the login screen.
 */

const UNSAFE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

function getCookie(name) {
  const match = document.cookie.split('; ').find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split('=')[1]) : null;
}

export async function apiFetch(url, { skipAuthEvent = false, ...options } = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const headers = { ...(options.headers || {}) };

  if (UNSAFE_METHODS.includes(method)) {
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) headers['X-CSRFToken'] = csrfToken;
  }

  const response = await fetch(url, { ...options, headers, credentials: 'include' });

  if ((response.status === 401 || response.status === 403) && !skipAuthEvent) {
    window.dispatchEvent(new Event('auth:expired'));
  }
  return response;
}
