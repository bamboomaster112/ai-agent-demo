import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Trash2 } from "lucide-react";
import { listSessions, deleteSession } from "../api/migrations";
import { DetectionBadge } from "../components/DetectionBadge";
import type { MigrationSession } from "../types/migration";

export function HistoryPage() {
  const [sessions, setSessions] = useState<MigrationSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSessions();
  }, []);

  async function loadSessions() {
    try {
      const data = await listSessions(100);
      setSessions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this migration session?")) return;
    try {
      await deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Migration History</h1>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : sessions.length === 0 ? (
        <div className="text-center py-12 bg-white border border-gray-200 rounded-lg">
          <p className="text-gray-500">No migrations yet</p>
          <Link
            to="/migrate/new"
            className="inline-block mt-2 text-blue-600 hover:text-blue-700 text-sm"
          >
            Start your first migration
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-lg hover:border-gray-300"
            >
              <Link to={`/migrate/${session.id}`} className="flex-1 min-w-0">
                <h3 className="font-medium text-gray-900 truncate">
                  {session.title || "Untitled Migration"}
                </h3>
                <div className="mt-2">
                  <DetectionBadge
                    platform={session.source_platform}
                    format={session.source_format}
                    configType={session.config_type}
                    confidence={session.detection_confidence}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  {new Date(session.created_at).toLocaleString()}
                </p>
              </Link>
              <div className="flex items-center gap-3">
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    session.status === "completed"
                      ? "bg-green-50 text-green-700"
                      : session.status === "failed"
                        ? "bg-red-50 text-red-700"
                        : "bg-yellow-50 text-yellow-700"
                  }`}
                >
                  {session.status}
                </span>
                <button
                  onClick={() => handleDelete(session.id)}
                  className="p-2 text-gray-400 hover:text-red-500"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
