import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getSessionDetail } from "../api/migrations";
import { useSSE } from "../hooks/useSSE";
import { ChatPanel } from "../components/ChatPanel";
import { YamlPreview } from "../components/YamlPreview";
import { DetectionBadge } from "../components/DetectionBadge";
import type { SessionDetail, Message, Workflow } from "../types/migration";

export function MigrationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [notes, setNotes] = useState<Array<{ level: string; text: string }>>([]);
  const [loading, setLoading] = useState(true);
  const { isStreaming, streamedText, startStream, stopStream } = useSSE();

  useEffect(() => {
    if (!id) return;
    getSessionDetail(id)
      .then((d) => {
        setDetail(d);
        setMessages(d.messages);
        setWorkflows(d.workflows);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  function handleSendMessage(content: string) {
    if (!id) return;

    // Optimistically add user message
    const userMsg: Message = {
      id: `temp-${Date.now()}`,
      role: "user",
      content,
      metadata: {},
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    startStream(
      id,
      content,
      // onToken
      () => {},
      // onYaml
      (filename, yamlContent) => {
        setWorkflows((prev) => [
          ...prev,
          {
            id: `temp-${Date.now()}`,
            filename,
            yaml_content: yamlContent,
            notes: [],
            version: 1,
            created_at: new Date().toISOString(),
          },
        ]);
      },
      // onNote
      (level, text) => {
        setNotes((prev) => [...prev, { level, text }]);
      },
      // onDone
      () => {
        // Add assistant message from streamed text
        setMessages((prev) => [
          ...prev,
          {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: streamedText,
            metadata: {},
            created_at: new Date().toISOString(),
          },
        ]);
      },
      // onError
      (message) => {
        console.error("Stream error:", message);
      }
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        Session not found
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Chat panel (left) */}
      <div className="flex-1 flex flex-col border-r border-gray-200">
        {/* Session header */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <h2 className="font-semibold text-gray-900">
            {detail.session.title || "Migration Session"}
          </h2>
          <div className="mt-2">
            <DetectionBadge
              platform={detail.session.source_platform}
              format={detail.session.source_format}
              configType={detail.session.config_type}
              confidence={detail.session.detection_confidence}
            />
          </div>
        </div>

        <ChatPanel
          messages={messages}
          streamedText={streamedText}
          isStreaming={isStreaming}
          onSendMessage={handleSendMessage}
          onStopStream={stopStream}
        />
      </div>

      {/* Workflow panel (right) */}
      <div className="w-[480px] flex flex-col bg-white overflow-auto">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">Generated Workflows</h3>
        </div>
        <div className="p-4 space-y-4 overflow-auto flex-1">
          {workflows.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">
              {isStreaming
                ? "Generating workflow..."
                : "Send a message to start migration"}
            </p>
          ) : (
            workflows.map((wf) => (
              <YamlPreview
                key={wf.id}
                filename={wf.filename}
                content={wf.yaml_content}
                notes={wf.notes}
              />
            ))
          )}

          {/* Notes */}
          {notes.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">
                Migration Notes
              </h4>
              {notes.map((note, i) => (
                <div
                  key={i}
                  className={`p-2 rounded text-xs ${
                    note.level === "warning"
                      ? "bg-orange-50 text-orange-700"
                      : "bg-blue-50 text-blue-700"
                  }`}
                >
                  <span className="font-semibold uppercase">{note.level}: </span>
                  {note.text}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
