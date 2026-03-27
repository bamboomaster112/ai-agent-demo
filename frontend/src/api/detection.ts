import { apiFetch } from "./client";
import type { DetectionResult } from "../types/migration";

export async function detectPipeline(
  content: string,
  filename?: string
): Promise<DetectionResult> {
  return apiFetch("/api/detect/", {
    method: "POST",
    body: JSON.stringify({ content, filename }),
  });
}

export async function overrideDetection(
  sessionId: string,
  sourcePlatform: string,
  sourceFormat: string,
  configType: string
): Promise<void> {
  await apiFetch(`/api/detect/migrations/${sessionId}/detection`, {
    method: "PUT",
    body: JSON.stringify({
      source_platform: sourcePlatform,
      source_format: sourceFormat,
      config_type: configType,
    }),
  });
}

export async function confirmDetection(sessionId: string): Promise<void> {
  await apiFetch(`/api/detect/migrations/${sessionId}/confirm-detection`, {
    method: "POST",
  });
}
