/**
 * SSR-safe localStorage helpers.
 * All functions are no-ops on the server (window is undefined).
 */

const TOKEN_KEY   = "cg_access";
const REFRESH_KEY = "cg_refresh";
const SETTINGS_KEY = "cg_settings";

export interface StoredSettings {
  ollamaUrl: string;
  model: string;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setTokens(tokens: { access_token: string; refresh_token: string }) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, tokens.access_token);
  window.localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
}

export function clearTokens() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}

export function getSettings(): StoredSettings {
  if (typeof window === "undefined") return { ollamaUrl: "http://localhost:11434", model: "gemma2:2b" };
  try {
    const raw = window.localStorage.getItem(SETTINGS_KEY);
    if (raw) return JSON.parse(raw) as StoredSettings;
  } catch {}
  return { ollamaUrl: "http://localhost:11434", model: "gemma2:2b" };
}

export function saveSettings(s: StoredSettings) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(s));
}
