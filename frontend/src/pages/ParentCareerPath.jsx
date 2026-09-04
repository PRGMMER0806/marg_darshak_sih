import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

function ParentCareerPath() {
  const navigate = useNavigate();
  const { studentUsername } = useParams();

  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchCareerPath = async () => {
      try {
        const parentResponse = await api.get("/parent/home");

        const child = (parentResponse.data.children || []).find(
          (item) => item.student_username === studentUsername
        );

        if (!child || !child.student_id) {
          setError("Unable to identify this linked student.");
          return;
        }

        const response = await api.get(
          `/dashboard/${child.student_id}`
        );

        setDashboard(response.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load the career path."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchCareerPath();
  }, [studentUsername]);

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading career path...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">
          Career Path
        </h1>

        <p className="mt-3 text-red-600">{error}</p>
      </div>
    );
  }

  const result = dashboard.latest_result;
  const careers = result.top_3_recommendations || [];

  return (
    <div>
      <button
        type="button"
        onClick={() =>
          navigate(`/parent/progress/${studentUsername}`)
        }
        className="mb-5 text-sm font-semibold text-violet-600"
      >
        ← Back to Child Progress
      </button>

      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Career Discovery
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          {dashboard.student.username}'s Career Path
        </h1>

        <p className="mt-3 max-w-3xl text-slate-500">
          Explore the career directions identified from the assessment
          results.
        </p>
      </div>

      <div className="rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
          Top Direction
        </p>

        <h2 className="mt-3 text-3xl font-bold">
          {result.top_career.career_field}
        </h2>

        <p className="mt-3 text-violet-100">
          {result.top_career.match_score}% current match
        </p>

        <div className="mt-5 rounded-2xl bg-white/10 p-5">
          <p className="text-sm font-semibold">
            Student Persona
          </p>

          <p className="mt-2 text-lg font-bold">
            {result.persona.name}
          </p>

          <p className="mt-2 text-sm leading-6 text-violet-100">
            {result.persona.description}
          </p>
        </div>
      </div>

      <div className="mt-10">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Recommended Paths
        </p>

        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          3 Career Directions
        </h2>

        <div className="mt-6 grid gap-6 lg:grid-cols-3">
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

              <p className="mt-4 text-2xl font-bold text-violet-600">
                {career.confidence_pct}%
              </p>

              <div className="mt-3 h-2 rounded-full bg-slate-100">
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

              <p className="mt-5 text-sm leading-6 text-slate-500">
                Recommended from the student's assessment profile.
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-10 rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Parent Perspective
        </p>

        <h2 className="mt-2 text-2xl font-bold text-slate-900">
          Support Exploration
        </h2>

        <p className="mt-3 max-w-3xl leading-7 text-slate-500">
          These recommendations describe the student's current assessment
          direction. They are starting points for exploration, not fixed
          career decisions.
        </p>
      </div>
    </div>
  );
}

export default ParentCareerPath;