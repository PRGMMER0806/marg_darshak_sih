import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

function TeacherStudentProgress() {
  const navigate = useNavigate();
  const { studentUsername } = useParams();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchStudent = async () => {
      try {
        const response = await api.get(
          `/teacher/student/${studentUsername}`
        );

        setData(response.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load student information."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchStudent();
  }, [studentUsername]);

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading student progress...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">
          Student Progress
        </h1>

        <p className="mt-3 text-red-600">{error}</p>

        <button
          type="button"
          onClick={() => navigate("/teacher/dashboard")}
          className="mt-6 rounded-xl bg-violet-600 px-5 py-3 font-semibold text-white"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const result = data.latest_result;
  const history = data.attempt_history || [];

  if (!result) {
    return (
      <div>
        <button
          type="button"
          onClick={() => navigate("/teacher/dashboard")}
          className="mb-5 text-sm font-semibold text-violet-600"
        >
          ← Back to Class Dashboard
        </button>

        <div className="rounded-3xl bg-white p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Student Progress
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            {data.student.username}
          </h1>

          <p className="mt-4 text-slate-500">
            This student has not completed an assessment yet.
          </p>

          <button
            type="button"
            onClick={() =>
              navigate(
                `/teacher/guidance/${studentUsername}`
              )
            }
            className="mt-6 rounded-xl bg-violet-600 px-5 py-3 font-semibold text-white"
          >
            Open Guidance
          </button>
        </div>
      </div>
    );
  }

  const riasecNames = {
    R: "Realistic",
    I: "Investigative",
    A: "Artistic",
    S: "Social",
    E: "Enterprising",
    C: "Conventional",
  };

  return (
    <div>
      <button
        type="button"
        onClick={() => navigate("/teacher/dashboard")}
        className="mb-5 text-sm font-semibold text-violet-600"
      >
        ← Back to Class Dashboard
      </button>

      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Student Progress
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          {data.student.username}
        </h1>

        <p className="mt-3 text-slate-500">
          {data.student.class_name} · {data.student.school_id}
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            ASSESSMENTS
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {data.progress.total_attempts}
          </h2>
        </div>

        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            LATEST SCORE
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {data.progress.latest_score}%
          </h2>
        </div>

        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            CAREER
          </p>

          <h2 className="mt-3 text-xl font-bold text-slate-900">
            {data.progress.latest_career_field}
          </h2>
        </div>
      </div>

      <div className="mt-8 rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
          Current Direction
        </p>

        <h2 className="mt-3 text-3xl font-bold">
          {result.top_career.career_field}
        </h2>

        <p className="mt-3 text-violet-100">
          {result.top_career.match_score}% match
        </p>

        <p className="mt-5 max-w-3xl leading-7 text-violet-100">
          {result.summary}
        </p>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl bg-white p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Aptitude
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-900">
            Skills Profile
          </h2>

          <div className="mt-6 space-y-5">
            {Object.entries(
              result.statistical_evaluation.aptitude
            ).map(([skill, value]) => (
              <div key={skill}>
                <div className="mb-2 flex justify-between">
                  <span className="capitalize text-sm font-medium text-slate-700">
                    {skill}
                  </span>

                  <span className="text-sm font-bold text-slate-900">
                    {value}%
                  </span>
                </div>

                <div className="h-2 rounded-full bg-slate-100">
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
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-white p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            RIASEC
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-900">
            Interest Profile
          </h2>

          <div className="mt-6 space-y-5">
            {Object.entries(
              result.statistical_evaluation.riasec
            ).map(([trait, value]) => (
              <div key={trait}>
                <div className="mb-2 flex justify-between">
                  <span className="text-sm font-medium text-slate-700">
                    {riasecNames[trait] || trait}
                  </span>

                  <span className="text-sm font-bold text-slate-900">
                    {value}%
                  </span>
                </div>

                <div className="h-2 rounded-full bg-slate-100">
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
            ))}
          </div>
        </div>
      </div>

      <div className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Career Directions
        </p>

        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          Top 3 Recommendations
        </h2>

        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          {(result.top_3_recommendations || []).map(
            (career, index) => (
              <div
                key={`${career.career_field}-${career.rank}`}
                className={`rounded-3xl p-6 ${
                  index === 0
                    ? "bg-violet-50 ring-2 ring-violet-500"
                    : "bg-slate-50"
                }`}
              >
                <p className="text-sm font-bold text-violet-600">
                  PATH {index + 1}
                </p>

                <h3 className="mt-3 text-xl font-bold text-slate-900">
                  {career.career_field}
                </h3>

                <p className="mt-4 text-2xl font-bold text-violet-600">
                  {career.confidence_pct}%
                </p>
              </div>
            )
          )}
        </div>
      </div>

      <div className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Assessment History
        </p>

        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[600px] text-left">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="pb-4 text-sm text-slate-500">
                  #
                </th>

                <th className="pb-4 text-sm text-slate-500">
                  Date
                </th>

                <th className="pb-4 text-sm text-slate-500">
                  Career
                </th>

                <th className="pb-4 text-sm text-slate-500">
                  Score
                </th>
              </tr>
            </thead>

            <tbody>
              {history.map((attempt, index) => (
                <tr
                  key={attempt.attempt_id}
                  className="border-b border-slate-100"
                >
                  <td className="py-4 text-sm text-slate-700">
                    {index + 1}
                  </td>

                  <td className="py-4 text-sm text-slate-500">
                    {new Date(
                      attempt.taken_at
                    ).toLocaleDateString("en-IN")}
                  </td>

                  <td className="py-4 text-sm font-semibold text-slate-900">
                    {attempt.career_field}
                  </td>

                  <td className="py-4 text-sm font-bold text-violet-600">
                    {attempt.score}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <button
        type="button"
        onClick={() =>
          navigate(`/teacher/guidance/${studentUsername}`)
        }
        className="mt-8 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white transition hover:bg-violet-700"
      >
        Open Career Guidance
      </button>
    </div>
  );
}

export default TeacherStudentProgress;