import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function TeacherHome() {
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHome = async () => {
      try {
        const [homeResponse, dashboardResponse] = await Promise.all([
          api.get("/teacher/home"),
          api.get("/teacher/dashboard"),
        ]);

        setData(homeResponse.data);
        setDashboard(dashboardResponse.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load teacher information."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchHome();
  }, []);

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading your command center...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">
          Teacher Portal
        </h1>

        <p className="mt-3 text-red-600">{error}</p>
      </div>
    );
  }

  const statistics = dashboard?.statistics || {};

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          The Command Center
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Welcome, {data.username}.
        </h1>

        <p className="mt-3 max-w-3xl text-slate-500">
          Monitor your class, understand student progress, and support career
          development through assessment insights.
        </p>
      </div>

      <div className="mb-8 grid gap-6 md:grid-cols-3">
        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            STUDENTS
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {statistics.total_students || 0}
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Students in {data.class_name || "your class"}
          </p>
        </div>

        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            ASSESSED
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {statistics.completed_assessment || 0}
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Students with completed assessments
          </p>
        </div>

        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            NOT APPEARED
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {statistics.not_appeared || 0}
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Students needing follow-up
          </p>
        </div>
      </div>

      <div className="rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
          CLASS OVERVIEW
        </p>

        <h2 className="mt-3 text-3xl font-bold">
          {data.class_name || "Class"}
        </h2>

        <p className="mt-3 max-w-2xl leading-7 text-violet-100">
          Review student assessment results, identify students who may need
          attention, and explore their career directions.
        </p>

        <button
          type="button"
          onClick={() => navigate("/teacher/dashboard")}
          className="mt-6 rounded-xl bg-white px-6 py-3 font-semibold text-violet-700 transition hover:bg-violet-50"
        >
          Open Class Dashboard
        </button>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <div className="rounded-3xl bg-white p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            FOLLOW-UP
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-900">
            Students needing attention
          </h2>

          <p className="mt-3 text-slate-500">
            View students who have not completed their assessment yet.
          </p>

          <button
            type="button"
            onClick={() => navigate("/teacher/not-appeared")}
            className="mt-6 rounded-xl border border-violet-200 px-5 py-3 font-semibold text-violet-700 transition hover:bg-violet-50"
          >
            View Not Appeared
          </button>
        </div>

        <div className="rounded-3xl bg-white p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            COMMUNICATION
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-900">
            Stay informed
          </h2>

          <p className="mt-3 text-slate-500">
            Check important notifications connected to your teacher portal.
          </p>

          <button
            type="button"
            onClick={() => navigate("/teacher/notifications")}
            className="mt-6 rounded-xl border border-violet-200 px-5 py-3 font-semibold text-violet-700 transition hover:bg-violet-50"
          >
            Open Notifications
          </button>
        </div>
      </div>
    </div>
  );
}

export default TeacherHome;