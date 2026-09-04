import { useEffect, useState } from "react";
import api from "../services/api";

function Guidance() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchGuidanceData = async () => {
      try {
        const userId = localStorage.getItem("user_id");

        if (!userId) {
          setError("Student ID not found. Please log in again.");
          return;
        }

        const response = await api.get(`/dashboard/${userId}`);

        setDashboard(response.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load your guidance."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchGuidanceData();
  }, []);

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading your guidance...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">
          Guidance
        </h1>

        <p className="mt-3 text-red-600">
          {error}
        </p>
      </div>
    );
  }

  const result = dashboard.latest_result;
  const careers = result.top_3_recommendations || [];

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Your Guide
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Career Guidance
        </h1>

        <p className="mt-3 max-w-3xl text-slate-500">
          Turn your assessment results into a practical plan for exploring
          your future.
        </p>
      </div>

      <div className="rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
          Current Direction
        </p>

        <h2 className="mt-3 text-3xl font-bold">
          {result.top_career.career_field}
        </h2>

        <p className="mt-3 text-violet-100">
          {result.top_career.match_score}% current match
        </p>

        <p className="mt-5 max-w-3xl leading-7 text-violet-100">
          {result.summary}
        </p>
      </div>

      <div className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Guidance Assistant
          </p>

          <h2 className="mt-2 text-3xl font-bold text-slate-900">
            Your Personalized Career Guide
          </h2>

          <p className="mt-3 max-w-2xl text-slate-500">
            Your guidance plan will be created using your assessment profile,
            career interests, and progress.
          </p>
        </div>

        <div className="rounded-2xl bg-slate-50 p-6">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-violet-100 text-xl text-violet-700">
              AI
            </div>

            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Guidance Agent
              </h3>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                Your AI career guide will analyze your results and create a
                step-by-step roadmap designed around your current stage and
                career interests.
              </p>

              <span className="mt-4 inline-block rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                GUIDANCE AGENT COMING NEXT
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Career Options
          </p>

          <h2 className="mt-2 text-3xl font-bold text-slate-900">
            Paths You Can Explore
          </h2>

          <p className="mt-2 text-slate-500">
            Your guidance can be built around any of these recommended paths.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {careers.map((career, index) => (
            <div
              key={`${career.career_field}-${career.rank}`}
              className={`rounded-3xl bg-white p-7 shadow-sm ${
                index === 0
                  ? "ring-2 ring-violet-500"
                  : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-violet-50 font-bold text-violet-700">
                  {index + 1}
                </div>

                {index === 0 && (
                  <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-bold text-violet-700">
                    TOP MATCH
                  </span>
                )}
              </div>

              <h3 className="mt-6 text-xl font-bold leading-7 text-slate-900">
                {career.career_field}
              </h3>

              <div className="mt-5">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm text-slate-500">
                    Match Score
                  </span>

                  <span className="font-bold text-violet-600">
                    {career.confidence_pct}%
                  </span>
                </div>

                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-violet-600"
                    style={{
                      width: `${Math.min(
                        Math.max(career.confidence_pct || 0, 0),
                        100
                      )}%`,
                    }}
                  />
                </div>
              </div>

              <button
                type="button"
                className="mt-6 w-full rounded-xl border border-violet-200 px-4 py-3 text-sm font-semibold text-violet-700 transition hover:bg-violet-50"
              >
                Explore This Path
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Roadmap Preview
        </p>

        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          Your Journey Ahead
        </h2>

        <p className="mt-3 max-w-2xl text-slate-500">
          The guidance agent will turn your selected career path into a
          detailed roadmap.
        </p>

        <div className="mt-8 grid gap-6 md:grid-cols-3">
          <div className="rounded-2xl bg-slate-50 p-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 font-bold text-violet-700">
              1
            </div>

            <h3 className="mt-4 text-lg font-bold text-slate-900">
              Understand
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Understand the career, required skills, subjects, and
              opportunities.
            </p>
          </div>

          <div className="rounded-2xl bg-slate-50 p-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 font-bold text-violet-700">
              2
            </div>

            <h3 className="mt-4 text-lg font-bold text-slate-900">
              Build
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Build the skills, experience, projects, and knowledge needed
              for your direction.
            </p>
          </div>

          <div className="rounded-2xl bg-slate-50 p-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 font-bold text-violet-700">
              3
            </div>

            <h3 className="mt-4 text-lg font-bold text-slate-900">
              Progress
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Track milestones and adjust your career plan as you grow.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Guidance;