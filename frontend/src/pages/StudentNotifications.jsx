import { useEffect, useState } from "react";
import api from "../services/api";

function StudentNotifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/notify/");

      setNotifications(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load notifications."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const acknowledgeNotification = async (notificationId) => {
    try {
      setError("");

      await api.post(
        `/notify/${notificationId}/acknowledge`
      );

      setNotifications((current) =>
        current.map((notification) =>
          notification._id === notificationId
            ? { ...notification, read: true }
            : notification
        )
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to update notification."
      );
    }
  };

  const unreadCount = notifications.filter(
    (notification) => !notification.read
  ).length;

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-4xl">

        {/* Header */}
        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Notifications
          </p>

          <div className="mt-2 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">
                Your Notifications
              </h1>

              <p className="mt-2 text-slate-500">
                Stay updated on your career journey.
              </p>
            </div>

            <div className="rounded-2xl bg-violet-100 px-4 py-3 text-center">
              <p className="text-2xl font-bold text-violet-700">
                {unreadCount}
              </p>

              <p className="text-xs font-medium text-violet-600">
                Unread
              </p>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-2xl bg-red-50 px-5 py-4 text-sm text-red-600">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading ? (
          <div className="rounded-3xl bg-white p-8 text-center shadow-sm">
            <p className="text-slate-500">
              Loading notifications...
            </p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="rounded-3xl bg-white p-10 text-center shadow-sm">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-violet-100 text-2xl">
              🔔
            </div>

            <h2 className="text-xl font-semibold text-slate-900">
              You're all caught up
            </h2>

            <p className="mt-2 text-slate-500">
              You don't have any notifications yet.
            </p>
          </div>
        ) : (
          <div className="space-y-4">

            {notifications.map((notification) => (
              <div
                key={notification._id}
                className={`rounded-3xl border p-5 shadow-sm transition ${
                  notification.read
                    ? "border-slate-200 bg-white"
                    : "border-violet-200 bg-violet-50"
                }`}
              >
                <div className="flex items-start justify-between gap-4">

                  <div className="flex gap-4">

                    <div
                      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${
                        notification.read
                          ? "bg-slate-100"
                          : "bg-violet-200"
                      }`}
                    >
                      🔔
                    </div>

                    <div>

                      <div className="flex flex-wrap items-center gap-2">

                        <span className="font-semibold text-slate-900">
                          {notification.type}
                        </span>

                        {!notification.read && (
                          <span className="rounded-full bg-violet-600 px-2 py-1 text-xs font-semibold text-white">
                            New
                          </span>
                        )}

                      </div>

                      <p className="mt-2 text-slate-600">
                        {notification.message}
                      </p>

                      {notification.created_at && (
                        <p className="mt-2 text-xs text-slate-400">
                          {new Date(
                            notification.created_at
                          ).toLocaleString()}
                        </p>
                      )}

                    </div>
                  </div>

                  {!notification.read && (
                    <button
                      type="button"
                      onClick={() =>
                        acknowledgeNotification(
                          notification._id
                        )
                      }
                      className="shrink-0 rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-violet-700"
                    >
                      Mark as read
                    </button>
                  )}

                </div>
              </div>
            ))}

          </div>
        )}

      </div>
    </div>
  );
}

export default StudentNotifications;