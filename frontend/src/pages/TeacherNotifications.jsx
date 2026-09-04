import { useEffect, useState } from "react";

import api from "../services/api";

function TeacherNotifications() {
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const response = await api.get(
          "/notify/unread-count"
        );

        setCount(response.data.unread_count || 0);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load notifications."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchNotifications();
  }, []);

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading notifications...
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Updates
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Notifications
        </h1>

        <p className="mt-3 text-slate-500">
          Stay informed about important teacher portal updates.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-2xl bg-red-50 p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          UNREAD
        </p>

        <h2 className="mt-3 text-4xl font-bold text-slate-900">
          {count}
        </h2>

        <p className="mt-2 text-slate-500">
          unread notification{count === 1 ? "" : "s"}
        </p>
      </div>

      <div className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Notification Center
        </p>

        <h2 className="mt-2 text-2xl font-bold text-slate-900">
          Updates will appear here
        </h2>

        <p className="mt-3 text-slate-500">
          The current notification integration exposes the unread-count
          endpoint. Detailed notification management remains part of the
          shared cross-role integration.
        </p>
      </div>
    </div>
  );
}

export default TeacherNotifications;