import { useEffect, useState } from "react";
import { getAnalytics } from "../../api/admin";
import type { Analytics } from "../../types/admin";

export function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAnalytics()
      .then(setAnalytics)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-gray-400">Loading...</div>;
  }

  if (!analytics) {
    return <div className="p-8 text-center text-gray-400">Failed to load analytics</div>;
  }

  const stats = [
    { label: "Total Users", value: analytics.total_users },
    { label: "Total Migrations", value: analytics.total_migrations },
    { label: "Total Messages", value: analytics.total_messages },
    { label: "Input Tokens", value: analytics.total_tokens_in.toLocaleString() },
    { label: "Output Tokens", value: analytics.total_tokens_out.toLocaleString() },
  ];

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Analytics</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-5 gap-4 mb-8">
        {stats.map((stat) => (
          <div key={stat.label} className="p-4 bg-white border border-gray-200 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {analytics.recent_activity.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-400 text-sm">
              No activity yet
            </div>
          ) : (
            analytics.recent_activity.map((activity, i) => (
              <div key={i} className="px-6 py-3 flex items-center justify-between">
                <div>
                  <span className="text-sm text-gray-900 font-medium">
                    {activity.action}
                  </span>
                  {activity.model_used && (
                    <span className="ml-2 text-xs text-gray-400">
                      {activity.model_used}
                    </span>
                  )}
                </div>
                <div className="text-right">
                  <span className="text-xs text-gray-500">
                    {activity.tokens_in > 0 &&
                      `${activity.tokens_in} in / ${activity.tokens_out} out`}
                  </span>
                  <p className="text-xs text-gray-400">
                    {new Date(activity.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
