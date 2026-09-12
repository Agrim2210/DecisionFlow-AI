const viteEnv = (
  import.meta as ImportMeta & {
    env?: Record<string, string | boolean | undefined>;
  }
).env;

const DEFAULT_PROD_API_URL = "https://decisionflow-api-gxmu.onrender.com/api/v1";

export function getApiBaseUrl() {
  if (viteEnv?.VITE_API_BASE_URL) {
    return String(viteEnv.VITE_API_BASE_URL).replace(/\/$/, "");
  }
  if (typeof window === "undefined") {
    // In SSR (Cloudflare Workers / Nitro), connect to live Render API
    return DEFAULT_PROD_API_URL;
  }
  // In client browser, check if running locally or in cloud
  const isLocal =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";
  if (viteEnv?.DEV && isLocal) {
    return "/api/v1";
  }
  if (isLocal) {
    return "http://localhost:8000/api/v1";
  }
  return DEFAULT_PROD_API_URL;
}

const ACCESS_TOKEN_KEY = "decisionflow.access_token";
const REFRESH_TOKEN_KEY = "decisionflow.refresh_token";

export type ApiRecord = Record<string, unknown>;

export class ApiError extends Error {
  status: number;
  details: unknown;
  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export function getAccessToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

function saveTokens(tokens?: ApiRecord | null) {
  if (typeof window === "undefined" || !tokens) return;
  const access = tokens.access_token ?? tokens.accessToken;
  const refresh = tokens.refresh_token ?? tokens.refreshToken;
  if (typeof access === "string") window.localStorage.setItem(ACCESS_TOKEN_KEY, access);
  if (typeof refresh === "string") window.localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearSession() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function getRefreshToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

async function refreshSession() {
  const refreshToken = getRefreshToken();
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}/identity/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: refreshToken ? JSON.stringify({ refresh_token: refreshToken }) : JSON.stringify({}),
  });
  if (!response.ok) throw new ApiError("Your session has expired.", response.status);
  const payload = (await response.json()) as ApiRecord;
  saveTokens((payload.tokens as ApiRecord | undefined) ?? payload);
  return payload;
}

type RequestOptions = RequestInit & { skipRefresh?: boolean };

export async function apiRequest<T = unknown>(
  path: string,
  options: RequestOptions = {},
  retried = false,
): Promise<T> {
  const headers = new Headers(options.headers);
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  if (!isFormData && options.body && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
  if (response.status === 401 && !retried && !options.skipRefresh) {
    try {
      await refreshSession();
      return apiRequest<T>(path, options, true);
    } catch {
      clearSession();
    }
  }
  const raw = await response.text();
  let payload: unknown = null;
  if (raw) {
    try {
      payload = JSON.parse(raw);
    } catch {
      payload = raw;
    }
  }
  if (!response.ok) {
    const record = payload && typeof payload === "object" ? (payload as ApiRecord) : undefined;
    const detail = record?.detail ?? record?.message;
    throw new ApiError(
      typeof detail === "string" ? detail : `Request failed (${response.status}).`,
      response.status,
      payload,
    );
  }
  return payload as T;
}

function authRequest(path: string, body: ApiRecord) {
  return apiRequest<ApiRecord>(path, {
    method: "POST",
    body: JSON.stringify(body),
    skipRefresh: true,
  }).then((payload) => {
    saveTokens((payload.tokens as ApiRecord | undefined) ?? payload);
    return payload;
  });
}

export const api = {
  // ── Auth ──────────────────────────────────────────────
  login: (body: { email: string; password: string }) => authRequest("/identity/auth/login", body),
  forgotPassword: (body: { email: string }) =>
    apiRequest<{ message: string }>("/identity/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify(body),
      skipRefresh: true,
    }),
  register: (body: {
    org_name: string;
    org_slug: string;
    name: string;
    email: string;
    password: string;
  }) => authRequest("/identity/auth/register", body),
  me: () => apiRequest<ApiRecord>("/identity/auth/me"),
  logout: () =>
    apiRequest("/identity/auth/logout", {
      method: "POST",
      body: JSON.stringify({ logout_all: false }),
      skipRefresh: true,
    }).finally(clearSession),

  // ── Analytics ─────────────────────────────────────────
  dashboard: () => apiRequest<ApiRecord>("/analytics/me"),
  orgDashboard: () => apiRequest<ApiRecord>("/analytics/dashboard"),
  taskAnalytics: () => apiRequest<ApiRecord>("/analytics/me/upcoming"),
  trend: () => apiRequest<ApiRecord>("/analytics/me/reliability"),

  // ── Meetings ──────────────────────────────────────────
  myMeetings: (params?: { limit?: number; cursor?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.cursor) q.set("cursor", params.cursor);
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return apiRequest<unknown>(`/meetings/mine${qs ? `?${qs}` : ""}`);
  },
  allMeetings: (params?: { limit?: number; cursor?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.cursor) q.set("cursor", params.cursor);
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return apiRequest<unknown>(`/meetings${qs ? `?${qs}` : ""}`);
  },
  meetings: () => apiRequest<unknown>("/meetings/mine?limit=8"),
  meetingDetail: (meetingId: string) => apiRequest<ApiRecord>(`/meetings/${meetingId}`),
  meetingStatus: (meetingId: string) => apiRequest<ApiRecord>(`/meetings/${meetingId}/status`),
  meetingExtraction: (meetingId: string) =>
    apiRequest<ApiRecord>(`/meetings/${meetingId}/extraction`),
  meetingTasks: (meetingId: string) => apiRequest<unknown>(`/meetings/${meetingId}/tasks`),
  meetingDecisions: (meetingId: string) => apiRequest<unknown>(`/meetings/${meetingId}/decisions`),
  meetingRisks: (meetingId: string) => apiRequest<unknown>(`/meetings/${meetingId}/risks`),
  meetingQuestions: (meetingId: string) =>
    apiRequest<unknown>(`/meetings/${meetingId}/questions`),
  deleteMeeting: (meetingId: string) =>
    apiRequest<void>(`/meetings/${meetingId}`, { method: "DELETE" }),
  retryMeeting: (meetingId: string) =>
    apiRequest<ApiRecord>(`/meetings/${meetingId}/retry`, { method: "POST" }),
  uploadMeeting: (form: FormData) =>
    apiRequest<ApiRecord>("/meetings/upload", { method: "POST", body: form }),
  pasteMeeting: (body: { title: string; text: string; meeting_date?: string; source?: string }) =>
    apiRequest<ApiRecord>("/meetings/paste", { method: "POST", body: JSON.stringify(body) }),

  // ── Tasks ─────────────────────────────────────────────
  myTasks: () => apiRequest<unknown>("/tasks/mine?limit=20"),
  allTasks: (params?: { limit?: number; cursor?: string; owner_id?: string; status?: string; overdue_only?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.cursor) q.set("cursor", params.cursor);
    if (params?.owner_id) q.set("owner_id", params.owner_id);
    if (params?.status) q.set("status", params.status);
    if (params?.overdue_only) q.set("overdue_only", "true");
    const qs = q.toString();
    return apiRequest<unknown>(`/tasks${qs ? `?${qs}` : ""}`);
  },
  taskDetail: (taskId: string) => apiRequest<ApiRecord>(`/tasks/${taskId}`),
  updateTaskStatus: (taskId: string, status: string) =>
    apiRequest<ApiRecord>(`/tasks/${taskId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  updateTask: (taskId: string, body: { title?: string; description?: string; due_date?: string }) =>
    apiRequest<ApiRecord>(`/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  assignTask: (taskId: string, body: { owner_id: string }) =>
    apiRequest<ApiRecord>(`/tasks/${taskId}/assign`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  // ── Notifications ─────────────────────────────────────
  notificationsUnread: () => apiRequest<unknown>("/notifications/unread"),
  notifications: (params?: { limit?: number; cursor?: string; unread_only?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.cursor) q.set("cursor", params.cursor);
    if (params?.unread_only) q.set("unread_only", "true");
    const qs = q.toString();
    return apiRequest<unknown>(`/notifications${qs ? `?${qs}` : ""}`);
  },
  markNotificationRead: (notificationId: string) =>
    apiRequest<ApiRecord>(`/notifications/${notificationId}/read`, { method: "PATCH" }),
  markAllNotificationsRead: () =>
    apiRequest<ApiRecord>("/notifications/read-all", { method: "PATCH" }),

  // ── Search ────────────────────────────────────────────
  search: (
    query: string,
    options: {
      mode?: "semantic" | "keyword" | "hybrid";
      source_type?: "meeting" | "decision" | "action_item" | "risk" | "question";
      limit?: number;
    } = {},
  ) =>
    apiRequest<unknown>("/search", {
      method: "POST",
      body: JSON.stringify({
        query,
        mode: options.mode ?? "semantic",
        limit: options.limit ?? 8,
        ...(options.source_type ? { source_type: options.source_type } : {}),
      }),
    }),
  searchSuggest: (query: string) =>
    apiRequest<unknown>("/search/suggest", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),

  // ── Users & Workspace ─────────────────────────────────
  users: (params?: { role?: string; limit?: number; cursor?: string }) => {
    const query = new URLSearchParams();
    if (params?.role) query.set("role", params.role);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.cursor) query.set("cursor", params.cursor);
    const queryString = query.toString();
    return apiRequest<{ users: ApiRecord[]; has_next: boolean; total?: number }>(
      `/identity/users${queryString ? `?${queryString}` : ""}`,
    );
  },
  inviteUser: (body: {
    email: string;
    name: string;
    role: "viewer" | "member" | "admin";
    temp_password: string;
  }) =>
    apiRequest<{ message: string; email: string; verification_url?: string }>("/identity/users/invite", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  pendingUsers: () =>
    apiRequest<{ invitations: ApiRecord[] }>("/identity/users/pending"),
  cancelInvitation: (pendingId: string) =>
    apiRequest<void>(`/identity/users/pending/${pendingId}`, {
      method: "DELETE",
    }),
  changeUserRole: (userId: string, role: "viewer" | "member" | "admin") =>
    apiRequest<ApiRecord>(`/identity/users/${userId}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    }),
  deactivateUser: (userId: string) =>
    apiRequest<void>(`/identity/users/${userId}`, {
      method: "DELETE",
    }),

  // ── Profile & Password ────────────────────────────────
  updateProfile: (body: { name?: string; avatar_url?: string }) =>
    apiRequest<ApiRecord>("/identity/users/me/profile", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  changePassword: (body: { current_password: string; new_password: string }) =>
    apiRequest<ApiRecord>("/identity/users/me/change-password", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // ── Organization ──────────────────────────────────────
  orgSettings: () => apiRequest<ApiRecord>("/identity/orgs/me"),
  updateOrgSettings: (body: { name?: string; settings?: Record<string, unknown> }) =>
    apiRequest<ApiRecord>("/identity/orgs/me", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  // ── Audit Logs ────────────────────────────────────────
  auditLogs: (params?: { limit?: number; cursor?: string; actor_id?: string; aggregate_type?: string; event_type?: string }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.cursor) q.set("cursor", params.cursor);
    if (params?.actor_id) q.set("actor_id", params.actor_id);
    if (params?.aggregate_type) q.set("aggregate_type", params.aggregate_type);
    if (params?.event_type) q.set("event_type", params.event_type);
    const qs = q.toString();
    return apiRequest<unknown>(`/audit-logs${qs ? `?${qs}` : ""}`);
  },
  auditLogDetail: (logId: string) => apiRequest<ApiRecord>(`/audit-logs/${logId}`),
};

export function readData<T = unknown>(payload: unknown): T {
  if (payload && typeof payload === "object" && "data" in payload)
    return (payload as ApiRecord).data as T;
  return payload as T;
}

export function readArray(payload: unknown): ApiRecord[] {
  const value = readData<unknown>(payload);
  if (Array.isArray(value))
    return value.filter((item): item is ApiRecord => Boolean(item && typeof item === "object"));
  if (value && typeof value === "object") {
    const record = value as ApiRecord;
    for (const key of [
      "users",
      "invitations",
      "items",
      "results",
      "tasks",
      "meetings",
      "notifications",
      "snapshots",
      "suggestions",
      "data",
    ]) {
      if (Array.isArray(record[key]))
        return record[key].filter((item): item is ApiRecord =>
          Boolean(item && typeof item === "object"),
        );
    }
  }
  return [];
}

export function readValue(record: ApiRecord | undefined, keys: string[], fallback = "") {
  if (!record) return fallback;
  for (const key of keys) {
    const value = record[key];
    if (value !== undefined && value !== null && value !== "") return String(value);
  }
  return fallback;
}

export function readNumber(record: ApiRecord | undefined, keys: string[], fallback = 0) {
  const value = readValue(record, keys, "");
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}
