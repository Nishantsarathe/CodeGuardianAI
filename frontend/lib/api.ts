/**
 * Lightweight browser API client.
 *
 * Uses the Next.js rewrite proxy so every request goes to
 * /api/backend/<path> → <NEXT_PUBLIC_API_URL>/api/v1/<path>
 *
 * Token storage uses SSR-safe helpers from @/lib/storage.
 */

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
}

// Re-export token helpers so other modules have a single import
export { getAccessToken as getToken, setTokens, clearTokens } from "@/lib/storage";

import { getAccessToken, setTokens, clearTokens } from "@/lib/storage";

export class APIError extends Error {
  status: number;
  data: any;
  constructor(message: string, status: number, data: any) {
    super(message);
    this.name = "APIError";
    this.status = status;
    this.data = data;
  }
}

function buildUrl(path: string): string {
  // Relative path — go through the Next.js rewrite proxy
  return `/api/backend${path.startsWith("/") ? path : `/${path}`}`;
}

async function request<T = any>(path: string, opts: RequestInit = {}): Promise<T> {
  const url = buildUrl(path);
  const headers = new Headers(opts.headers || {});

  // Set Content-Type only for requests that have a body and haven't set it manually
  if (!(opts.body instanceof FormData)) {
    headers.set("Content-Type", headers.get("Content-Type") ?? "application/json");
  }

  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(url, { ...opts, headers, cache: "no-store" });

  const text = await res.text();
  const data = text ? safeJson(text) : null;

  if (!res.ok) {
    const message =
      data?.detail?.message ??
      data?.detail ??
      data?.message ??
      res.statusText ??
      "Request failed";
    throw new APIError(String(message), res.status, data);
  }

  return data as T;
}

function safeJson(text: string): any {
  try { return JSON.parse(text); } catch { return text; }
}

function qs(params: Record<string, string | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") q.set(k, v);
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}

export const api = {
  // Raw helpers
  get:  <T = any>(path: string) => request<T>(path),
  post: <T = any>(path: string, body?: any) =>
    request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined }),
  put:  <T = any>(path: string, body?: any) =>
    request<T>(path, { method: "PUT", body: body !== undefined ? JSON.stringify(body) : undefined }),
  del:  <T = any>(path: string) => request<T>(path, { method: "DELETE" }),

  // ── Auth ─────────────────────────────────────────────────────────────────
  login: (username_or_email: string, password: string) =>
    request<AuthTokens>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username_or_email, password }),
    }),
  register: (payload: {
    email: string; username: string; password: string;
    full_name?: string; role?: string;
  }) => request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request("/auth/me"),
  refresh: (refresh_token: string) =>
    request<AuthTokens>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    }),

  // ── Projects ─────────────────────────────────────────────────────────────
  listProjects: (search?: string) =>
    request(`/projects${qs({ search })}`),
  createProject: (payload: {
    name: string; source_type: string; source_ref?: string;
    description?: string; language?: string;
  }) => request("/projects", { method: "POST", body: JSON.stringify(payload) }),
  getProject: (id: string) => request(`/projects/${id}`),
  projectStats: (id: string) => request(`/projects/${id}/stats`),
  deleteProject: (id: string) => request(`/projects/${id}`, { method: "DELETE" }),

  // ── Analyses ─────────────────────────────────────────────────────────────
  listAnalyses: (projectId: string) => request(`/analyses?project_id=${projectId}`),
  createAnalysis: (project_id: string, config: Record<string, any> = {}) =>
    request("/analyses", { method: "POST", body: JSON.stringify({ project_id, config }) }),
  getAnalysis: (id: string) => request(`/analyses/${id}`),
  getStatus:   (id: string) => request(`/analyses/${id}/status`),
  deleteAnalysis: (id: string) => request(`/analyses/${id}`, { method: "DELETE" }),

  // ── Agents ───────────────────────────────────────────────────────────────
  listAgents: () => request("/agents"),
  listFindings: (analysisId: string, opts: { agent?: string; severity?: string } = {}) =>
    request(`/agents/findings/${analysisId}${qs({ agent: opts.agent, severity: opts.severity })}`),
  reRunAgent: (analysisId: string, agent: string) =>
    request(`/agents/runs/${analysisId}/${agent}`, { method: "POST" }),

  // ── Chat ─────────────────────────────────────────────────────────────────
  listSessions:  () => request("/chat/sessions"),
  createSession: (analysis_id?: string, title = "New chat") =>
    request("/chat/sessions", { method: "POST", body: JSON.stringify({ analysis_id, title }) }),
  getSession:    (id: string) => request(`/chat/sessions/${id}`),
  postMessage:   (sessionId: string, content: string) =>
    request(`/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
  deleteSession: (id: string) => request(`/chat/sessions/${id}`, { method: "DELETE" }),

  // ── Dashboard ────────────────────────────────────────────────────────────
  dashboard: () => request("/dashboard/summary"),

  // ── Users (admin only) ──────────────────────────────────────────────────
  listUsers: () => request("/users"),
  updateUserRole: (userId: string, role: "admin" | "reviewer" | "viewer") =>
    request(`/users/${userId}/role`, { method: "PATCH", body: JSON.stringify({ role }) }),

  // ── Uploads ──────────────────────────────────────────────────────────────
  uploadFile: (file: File, projectName?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (projectName) fd.append("project_name", projectName);
    return request("/uploads/file", { method: "POST", body: fd });
  },
  uploadZip: (file: File, projectName?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (projectName) fd.append("project_name", projectName);
    return request("/uploads/zip", { method: "POST", body: fd });
  },
};
