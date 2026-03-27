import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PlusCircle, ArrowRight } from "lucide-react";
import { listSessions } from "../api/migrations";
import { useAuth } from "../auth/AuthProvider";
import { DetectionBadge } from "../components/DetectionBadge";
import type { MigrationSession } from "../types/migration";

export function DashboardPage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<MigrationSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listSessions(5)
      .then(setSessions)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome, {user?.display_name || "User"}
          </h1>
          <p className="text-gray-500 mt-1">
            Migrate your CI/CD pipelines to GitHub Actions
          </p>
        </div>
        <Link
          to="/migrate/new"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <PlusCircle className="h-4 w-4" />
          New Migration
        </Link>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        <Link
          to="/migrate/new"
          className="p-6 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition"
        >
          <h3 className="font-semibold text-gray-900">Jenkins to GitHub Actions</h3>
          <p className="text-sm text-gray-500 mt-1">
            Convert Jenkinsfile pipelines
          </p>
        </Link>
        <Link
          to="/migrate/new"
          className="p-6 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition"
        >
          <h3 className="font-semibold text-gray-900">TeamCity to GitHub Actions</h3>
          <p className="text-sm text-gray-500 mt-1">
            Convert Kotlin DSL, XML, or API configs
          </p>
        </Link>
      </div>

      {/* Recent migrations */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Migrations</h2>
          <Link to="/history" className="text-sm text-blue-600 hover:text-blue-700">
            View all
          </Link>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-400">Loading...</div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-12 bg-white border border-gray-200 rounded-lg">
            <p className="text-gray-500">No migrations yet</p>
            <Link
              to="/migrate/new"
              className="inline-flex items-center gap-1 mt-2 text-blue-600 hover:text-blue-700 text-sm"
            >
              Start your first migration <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <Link
                key={session.id}
                to={`/migrate/${session.id}`}
                className="block p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">
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
                  </div>
                  <div className="text-right">
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        session.status === "completed"
                          ? "bg-green-50 text-green-700"
                          : session.status === "failed"
                            ? "bg-red-50 text-red-700"
                            : "bg-yellow-50 text-yellow-700"
                      }`}
                    >
                      {session.status}
                    </span>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(session.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
