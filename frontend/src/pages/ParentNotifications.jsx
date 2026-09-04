import { useEffect, useState } from "react";
import api from "../services/api";

function ParentNotifications() {
  const [count, setCount] = useState(0);
  const [error, setError] = useState("");

  const fetchNotifications = async () => {
    try {
      const response = await api.get("/notify/unread-count");

      setCount(response.data.unread_count || 0);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load notifications."
      );
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Updates
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Notifications
        </h1>

        <p className="mt-3 max-w-3xl text-slate-500">
          Stay informed about important updates connected to your child's
          career journey.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl bg-red-50 p-4 text-sm text-red-600">
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
          The notification system currently exposes the unread-count
          endpoint. The detailed notification list and acknowledgement flow
          will be connected as part of the shared notification integration.
        </p>
      </div>
    </div>
  );
}

export default ParentNotifications;