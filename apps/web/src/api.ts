import type { Attempt } from "./types";

export async function api<T>(
  path: string,
  options: RequestInit = {},
  attempt?: Attempt,
  teacher = false,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (attempt) headers.set("X-Attempt-Token", attempt.token);
  if (teacher)
    headers.set(
      "X-Teacher-Key",
      import.meta.env.VITE_DEV_TEACHER_KEY || "monti-local-teacher",
    );
  const response = await fetch(`/api${path}`, { ...options, headers });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : `No se pudo completar la acción (${response.status}).`,
    );
  }
  return response.json();
}

export const post = (body?: unknown): RequestInit => ({
  method: "POST",
  ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
});
