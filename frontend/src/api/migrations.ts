import { apiFetch } from "./client";
import type { MigrationSession, SessionDetail, Message } from "../types/migration";

export async function createSession(
  sourceType: string,
  sourceContent?: string,
  title?: string
): Promise<MigrationSession> {
  return apiFetch("/api/migrations/", {
    method: "POST",
    body: JSON.stringify({
      source_type: sourceType,
      source_content: sourceContent,
      title,
    }),
  });
}

export async function listSessions(
  limit = 20,
  offset = 0
): Promise<MigrationSession[]> {
  return apiFetch(`/api/migrations/?limit=${limit}&offset=${offset}`);
}

export async function getSessionDetail(
  sessionId: string
): Promise<SessionDetail> {
  return apiFetch(`/api/migrations/${sessionId}`);
}

export async function deleteSession(sessionId: string): Promise<void> {
  await apiFetch(`/api/migrations/${sessionId}`, { method: "DELETE" });
}

export async function getMessages(sessionId: string): Promise<Message[]> {
  return apiFetch(`/api/migrations/${sessionId}/messages`);
}

export function sendMessageSSE(
  sessionId: string,
  content: string,
  accessToken: string
): EventSource {
  // We use fetch + ReadableStream for SSE since EventSource doesn't support POST
  // This is a helper that returns the URL for EventSource-compatible usage
  // Actually, we'll use a custom SSE approach in the useSSE hook
  const url = `/api/migrations/${sessionId}/messages`;
  return new EventSource(url); // Placeholder - actual SSE handled in useSSE hook
}
