import { useState, useCallback, useRef } from "react";
import { getAccessToken } from "../api/client";

interface SSEMessage {
  event: string;
  data: Record<string, unknown>;
}

export function useSSE() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState("");
  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = useCallback(
    async (
      sessionId: string,
      content: string,
      onToken: (text: string) => void,
      onYaml: (filename: string, yamlContent: string) => void,
      onNote: (level: string, text: string) => void,
      onDone: () => void,
      onError: (message: string) => void
    ) => {
      setIsStreaming(true);
      setStreamedText("");

      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const token = getAccessToken();
        const response = await fetch(`/api/migrations/${sessionId}/messages`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ content }),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";
        let fullText = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Parse SSE events from buffer
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let currentEvent = "";
          let currentData = "";

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              currentData = line.slice(6);
              try {
                const parsed = JSON.parse(currentData);

                switch (currentEvent) {
                  case "token":
                    fullText += parsed.text;
                    setStreamedText(fullText);
                    onToken(parsed.text);
                    break;
                  case "yaml":
                    onYaml(parsed.filename, parsed.content);
                    break;
                  case "note":
                    onNote(parsed.level, parsed.text);
                    break;
                  case "done":
                    onDone();
                    break;
                  case "error":
                    onError(parsed.message);
                    break;
                }
              } catch {
                // Ignore parse errors
              }
              currentEvent = "";
              currentData = "";
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          onError((err as Error).message || "Stream failed");
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    []
  );

  const stopStream = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return { isStreaming, streamedText, startStream, stopStream };
}
