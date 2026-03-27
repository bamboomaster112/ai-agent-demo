import { apiFetch } from "./client";
import type { Preference } from "../types/admin";

export async function listPreferences(): Promise<Preference[]> {
  return apiFetch("/api/users/me/preferences/");
}

export async function createPreference(
  category: string,
  preferenceKey: string,
  preferenceValue: string
): Promise<Preference> {
  return apiFetch("/api/users/me/preferences/", {
    method: "POST",
    body: JSON.stringify({
      category,
      preference_key: preferenceKey,
      preference_value: preferenceValue,
    }),
  });
}

export async function updatePreference(
  prefId: string,
  value: string
): Promise<Preference> {
  return apiFetch(`/api/users/me/preferences/${prefId}`, {
    method: "PUT",
    body: JSON.stringify({ preference_value: value }),
  });
}

export async function deletePreference(prefId: string): Promise<void> {
  await apiFetch(`/api/users/me/preferences/${prefId}`, { method: "DELETE" });
}

export async function extractPreferences(
  sessionId: string
): Promise<{ extracted: number; preferences: Preference[] }> {
  return apiFetch(`/api/users/me/preferences/extract/${sessionId}`, {
    method: "POST",
  });
}
