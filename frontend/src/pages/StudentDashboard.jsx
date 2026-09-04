import { useEffect, useState } from "react";
import api from "../services/api";

function StudentDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboard = async () => {
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
            "Unable to load your dashboard."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading your dashboard...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">
          Dashboard
        </h1>

        <p className="mt-3 text-red-600">
          {error}
        </p>
      </div>
    );
  }

  const progress = dashboard.progress;
  const result = dashboard.latest_result;
  const persona = result.persona;
  const careers = result.top_3_recommendations || [];
  const history = dashboard.attempt_history || [];

  const riasecNames = {
    R: "Realistic",
    I: "Investigative",
    A: "Artistic",
    S: "Social",
    E: "Enterprising",
    C: "Conventional",
  };

  const formatDate = (dateString) => {
    if (!dateString) {
      return "Unknown date";
    }

    return new Date(dateString).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Your Journey
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Welcome back, {dashboard.student.username}.
        </h1>

        <p className="mt-3 max-w-2xl text-slate-500">
          Keep exploring your strengths and discovering where they can take
          you.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            ASSESSMENTS
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {progress.total_attempts}
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Completed assessments
          </p>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            LATEST SCORE
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {progress.latest_score}%
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Your latest career match score
          </p>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            TOP CAREER
          </p>

          <h2 className="mt-3 text-xl font-bold text-slate-900">
            {progress.latest_career_field}
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Your current strongest career match
          </p>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            PERSONA
          </p>

          <h2 className="mt-3 text-xl font-bold text-slate-900">
            {persona.name}
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            {persona.description}
          </p>
        </div>
      </div>

      <div className="mt-8 rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
          Your Current Direction
        </p>

        <h2 className="mt-3 text-3xl font-bold">
          {result.top_career.career_field}
        </h2>

        <p className="mt-3 text-violet-100">
          Current match score: {result.top_career.match_score}%
        </p>

        <p className="mt-4 max-w-3xl leading-7 text-violet-100">
          {result.summary}
        </p>
      </div>

      <div className="mt-8">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Career Discovery
          </p>

          <h2 className="mt-2 text-3xl font-bold text-slate-900">
            Your 3 Career Paths
          </h2>

          <p className="mt-2 max-w-2xl text-slate-500">
            These career paths are matched to the strengths and interests
            identified in your assessment.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {careers.map((career, index) => (
            <div
              key={`${career.career_field}-${career.rank}`}
              className={`relative rounded-3xl bg-white p-7 shadow-sm ${
                index === 0 ? "ring-2 ring-violet-500" : ""
              }`}
            >
              {index === 0 && (
                <div className="absolute right-6 top-6 rounded-full bg-violet-100 px-3 py-1 text-xs font-bold text-violet-700">
                  TOP MATCH
                </div>
              )}

              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50 text-lg font-bold text-violet-700">
                {index + 1}
              </div>

              <p className="mt-6 text-sm font-semibold uppercase tracking-wide text-slate-400">
                Career Path {index + 1}
              </p>

              <h3 className="mt-2 pr-16 text-xl font-bold leading-7 text-slate-900">
                {career.career_field}
              </h3>

              <div className="mt-6">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-500">
                    Match Score
                  </span>

                  <span className="text-lg font-bold text-violet-600">
                    {career.confidence_pct}%
                  </span>
                </div>

                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-violet-600"
                    style={{
                      width: `${Math.min(
                        Math.max(career.confidence_pct, 0),
                        100
                      )}%`,
                    }}
                  />
                </div>
              </div>

              <p className="mt-6 text-sm leading-6 text-slate-500">
                This path is recommended based on your assessment profile
                and current career-match results.
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl bg-white p-8 shadow-sm">
          <div className="mb-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
              Assessment Skills
            </p>

            <h2 className="mt-2 text-2xl font-bold text-slate-900">
              Aptitude Evaluation
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Your performance across different reasoning abilities.
            </p>
          </div>

          <div className="space-y-5">
            {Object.entries(result.statistical_evaluation.aptitude).map(
              ([skill, value]) => (
                <div key={skill}>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium capitalize text-slate-700">
                      {skill}
                    </span>

                    <span className="text-sm font-semibold text-slate-900">
                      {value}%
                    </span>
                  </div>

                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-violet-600"
                      style={{
                        width: `${Math.min(
                          Math.max(value || 0, 0),
                          100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              )
            )}
          </div>
        </div>

        <div className="rounded-3xl bg-white p-8 shadow-sm">
          <div className="mb-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
              Interest Profile
            </p>

            <h2 className="mt-2 text-2xl font-bold text-slate-900">
              RIASEC Evaluation
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Your interest levels across six career personality areas.
            </p>
          </div>

          <div className="space-y-5">
            {Object.entries(result.statistical_evaluation.riasec).map(
              ([trait, value]) => (
                <div key={trait}>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-700">
                      {riasecNames[trait] || trait}
                    </span>

                    <span className="text-sm font-semibold text-slate-900">
                      {value}%
                    </span>
                  </div>

                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-violet-600"
                      style={{
                        width: `${Math.min(
                          Math.max(value || 0, 0),
                          100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              )
            )}
          </div>
        </div>
      </div>

      <div className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Your Progress
          </p>

          <h2 className="mt-2 text-3xl font-bold text-slate-900">
            Assessment History
          </h2>

          <p className="mt-2 text-slate-500">
            See how your career results have changed across your assessments.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[650px] text-left">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="pb-4 text-sm font-semibold text-slate-500">
                  #
                </th>

                <th className="pb-4 text-sm font-semibold text-slate-500">
                  Date
                </th>

                <th className="pb-4 text-sm font-semibold text-slate-500">
                  Career Path
                </th>

                <th className="pb-4 text-sm font-semibold text-slate-500">
                  Match Score
                </th>

                <th className="pb-4 text-sm font-semibold text-slate-500">
                  Status
                </th>
              </tr>
            </thead>

            <tbody>
              {history.map((attempt, index) => (
                <tr
                  key={attempt.attempt_id}
                  className="border-b border-slate-100 last:border-0"
                >
                  <td className="py-5 text-sm font-semibold text-slate-700">
                    {index + 1}
                  </td>

                  <td className="py-5 text-sm text-slate-500">
                    {formatDate(attempt.taken_at)}
                  </td>

                  <td className="py-5">
                    <p className="text-sm font-semibold text-slate-900">
                      {attempt.career_field}
                    </p>
                  </td>

                  <td className="py-5">
                    <span className="rounded-full bg-violet-50 px-3 py-1 text-sm font-semibold text-violet-700">
                      {attempt.score}%
                    </span>
                  </td>

                  <td className="py-5">
                    {index === 0 ? (
                      <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700">
                        Latest
                      </span>
                    ) : (
                      <span className="text-sm text-slate-400">
                        Completed
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {history.length === 0 && (
          <div className="rounded-2xl bg-slate-50 p-6 text-center">
            <p className="text-sm text-slate-500">
              No assessment history available yet.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default StudentDashboard;