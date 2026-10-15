/**
 * API client for MRPL AI Workbench
 * Communicates with the local Django REST Framework backend.
 */

import { apiFetch } from './http';

const API_BASE = import.meta.env.VITE_API_URL || '';

export async function sendMessage(message) {
  const url = `${API_BASE}/api/chat/`;

  try {
    const response = await apiFetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: data.error || data.message || `Server error (${response.status})`,
        status: response.status,
      };
    }

    return data;
  } catch (err) {
    return {
      success: false,
      error: "Unable to connect to Django backend. Ensure backend is running.",
      details: err.message,
    };
  }
}
