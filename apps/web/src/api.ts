import type { Attempt } from "./types";

const SESSION_KEY = "monti.session";

export type SessionUser = {
  id: string;
  login: string;
  display_name: string;
  role: "admin" | "teacher" | "student";
};

export type StoredSession = {
  token: string;
  user: SessionUser;
};

export function schoolAuthEnabled(): boolean {
  return String(import.meta.env.VITE_FEATURE_SCHOOL_AUTH || "false").toLowerCase() === "true";
}

export function loadSession(): StoredSession | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as StoredSession) : null;
  } catch {
    return null;
  }
}

export function saveSession(session: StoredSession | null) {
  if (!session) sessionStorage.removeItem(SESSION_KEY);
  else sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
  attempt?: Attempt,
  teacher = false,
  bearer?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (attempt) headers.set("X-Attempt-Token", attempt.token);
  const token = bearer ?? loadSession()?.token;
  if (token) headers.set("Authorization", `Bearer ${token}`);
  else if (teacher && !schoolAuthEnabled()) {
    headers.set(
      "X-Teacher-Key",
      import.meta.env.VITE_DEV_TEACHER_KEY || "monti-local-teacher",
    );
  }
  const response = await fetch(`/api${path}`, { ...options, headers });
  if (!response.ok) {
    if (response.status === 204) return undefined as T;
    const data = await response.json().catch(() => ({}));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : `No se pudo completar la acción (${response.status}).`,
    );
  }
  if (response.status === 204) return undefined as T;
  const text = await response.text();
  return text ? (JSON.parse(text) as T) : (undefined as T);
}

export const post = (body?: unknown): RequestInit => ({
  method: "POST",
  ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
});

export const patch = (body?: unknown): RequestInit => ({
  method: "PATCH",
  ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
});

export const del = (): RequestInit => ({ method: "DELETE" });
