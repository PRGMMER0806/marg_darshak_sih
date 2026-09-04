import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function ParentHome() {
  const navigate = useNavigate();

  const username = localStorage.getItem("username");

  const [children, setChildren] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchChildren = async () => {
      try {
        const response = await api.get("/parent/home");

        setChildren(response.data.children || []);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load your children's information."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchChildren();
  }, []);

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading your children's progress...
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          The Guide
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Welcome, {username || "Parent"}.
        </h1>

        <p className="mt-3 max-w-3xl text-slate-500">
          Stay connected with your child's progress, career discovery, and
          future direction.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-2xl bg-red-50 p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            CHILDREN
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {children.length}
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Linked student profiles
          </p>
        </div>

        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            LATEST SCORE
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {children.length > 0 && children[0].latest_score != null
              ? `${children[0].latest_score}%`
              : "—"}
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Latest available assessment score
          </p>
        </div>

        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            CAREER DIRECTION
          </p>

          <h2 className="mt-3 text-xl font-bold text-slate-900">
            {children.length > 0 && children[0].career_field
              ? children[0].career_field
              : "Awaiting Assessment"}
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Current strongest direction
          </p>
        </div>
      </div>

      <div className="mt-8 rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
          Parent Overview
        </p>

        <h2 className="mt-3 text-3xl font-bold">
          Support their career journey.
        </h2>

        <p className="mt-4 max-w-2xl leading-7 text-violet-100">
          Follow assessment progress, understand career recommendations,
          contribute useful observations, and stay informed about your
          child's development.
        </p>
      </div>

      <div className="mt-8">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Your Children
          </p>

          <h2 className="mt-2 text-3xl font-bold text-slate-900">
            Student Profiles
          </h2>

          <p className="mt-2 text-slate-500">
            Select a child to view their career journey.
          </p>
        </div>

        {children.length === 0 ? (
          <div className="rounded-3xl bg-white p-8 text-center shadow-sm">
            <h3 className="text-xl font-bold text-slate-900">
              No linked students yet
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Once a student is linked to your account, their progress will
              appear here.
            </p>
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            {children.map((child) => (
              <div
                key={child.student_username}
                className="rounded-3xl bg-white p-7 shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
                      STUDENT
                    </p>

                    <h3 className="mt-2 text-2xl font-bold text-slate-900">
                      {child.student_username}
                    </h3>
                  </div>

                  <div className="rounded-2xl bg-violet-50 px-4 py-2 text-sm font-bold text-violet-700">
                    {child.latest_score != null
                      ? `${child.latest_score}%`
                      : "No Score"}
                  </div>
                </div>

                <div className="mt-6 rounded-2xl bg-slate-50 p-5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Career Direction
                  </p>

                  <p className="mt-2 font-semibold text-slate-900">
                    {child.career_field || "Assessment not completed"}
                  </p>
                </div>

                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/parent/progress/${child.student_username}`
                      )
                    }
                    className="rounded-xl border border-violet-200 px-3 py-3 text-sm font-semibold text-violet-700 transition hover:bg-violet-50"
                  >
                    Progress
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/parent/career-path/${child.student_username}`
                      )
                    }
                    className="rounded-xl border border-violet-200 px-3 py-3 text-sm font-semibold text-violet-700 transition hover:bg-violet-50"
                  >
                    Career Path
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/parent/context/${child.student_username}`
                      )
                    }
                    className="rounded-xl border border-violet-200 px-3 py-3 text-sm font-semibold text-violet-700 transition hover:bg-violet-50"
                  >
                    Add Context
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Guidance
        </p>

        <h2 className="mt-2 text-2xl font-bold text-slate-900">
          Help shape their journey
        </h2>

        <p className="mt-3 max-w-2xl text-slate-500">
          Explore your child's career direction and provide useful context
          from your perspective.
        </p>

        {children.length > 0 && (
          <button
            type="button"
            onClick={() =>
              navigate(
                `/parent/guidance/${children[0].student_username}`
              )
            }
            className="mt-6 rounded-xl bg-violet-600 px-5 py-3 font-semibold text-white transition hover:bg-violet-700"
          >
            Open Guidance
          </button>
        )}
      </div>
    </div>
  );
}

export default ParentHome;