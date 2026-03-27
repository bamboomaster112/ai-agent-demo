import { apiFetch } from "./client";
import type { AdminUser, AIConfig, Analytics } from "../types/admin";

// Users
export async function listUsers(limit = 50, offset = 0): Promise<AdminUser[]> {
  return apiFetch(`/api/admin/users?limit=${limit}&offset=${offset}`);
}

export async function updateUser(
  userId: string,
  updates: { role?: string; is_active?: boolean }
): Promise<AdminUser> {
  return apiFetch(`/api/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });
}

// AI Config
export async function getAIConfig(): Promise<AIConfig[]> {
  return apiFetch("/api/admin/ai-config");
}

export async function updateAIConfig(
  key: string,
  value: Record<string, unknown>
): Promise<void> {
  await apiFetch("/api/admin/ai-config", {
    method: "PUT",
    body: JSON.stringify({ key, value }),
  });
}

// RAG Config
export async function getRAGConfig(): Promise<Record<string, unknown>> {
  return apiFetch("/api/rag/config");
}

export async function updateRAGConfig(
  key: string,
  value: Record<string, unknown>
): Promise<void> {
  await apiFetch("/api/rag/config", {
    method: "PUT",
    body: JSON.stringify({ key, value }),
  });
}

// Preview
export async function previewMigration(
  sampleInput: string,
  sourceType: string,
  overrides: Record<string, unknown> = {}
): Promise<{ output: string; model: string; usage: { input_tokens: number; output_tokens: number } }> {
  return apiFetch("/api/admin/preview", {
    method: "POST",
    body: JSON.stringify({
      sample_input: sampleInput,
      source_type: sourceType,
      overrides,
    }),
  });
}

// Analytics
export async function getAnalytics(): Promise<Analytics> {
  return apiFetch("/api/admin/analytics");
}
