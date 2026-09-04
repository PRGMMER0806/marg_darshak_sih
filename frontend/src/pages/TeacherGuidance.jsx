import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

function TeacherGuidance() {
  const navigate = useNavigate();
  const { studentUsername } = useParams();

  const [student, setStudent] = useState(null);
  const [context, setContext] = useState([]);
  const [grades, setGrades] = useState("");
  const [extracurricularNote, setExtracurricularNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchGuidance = async () => {
      try {
        const [studentResponse, contextResponse] =
          await Promise.all([
            api.get(
              `/teacher/student/${studentUsername}`
            ),
            api.get(
              `/teacher/context/${studentUsername}`
            ),
          ]);

        setStudent(studentResponse.data);
        setContext(contextResponse.data.contexts || []);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load career guidance."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchGuidance();
  }, [studentUsername]);

  const handleContextSubmit = async (e) => {
    e.preventDefault();

    setSaving(true);
    setMessage("");
    setError("");

    let academicGrades = null;

    if (grades.trim()) {
      try {
        academicGrades = JSON.parse(grades);
      } catch {
        setError(
          'Academic grades must be valid JSON, for example {"Math":85,"Science":90}.'
        );
        setSaving(false);
        return;
      }
    }

    try {
      await api.post("/teacher/context", {
        student_id: studentUsername,
        academic_grades: academicGrades,
        extracurricular_note:
          extracurricularNote || null,
      });

      setMessage(
        "Teacher context saved successfully."
      );

      setGrades("");
      setExtracurricularNote("");

      const response = await api.get(
        `/teacher/context/${studentUsername}`
      );

      setContext(response.data.contexts || []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to save teacher context."
      );
    } finally {
      setSaving(false);
    }
  };

  const handleFlag = async () => {
  console.log("FLAG BUTTON CLICKED");

  setMessage("");
  setError("");

  try {
    console.log("SENDING FLAG REQUEST");

    const response = await api.post(
      `/teacher/flag-followup/${studentUsername}`
    );

    console.log("FLAG RESPONSE:", response);

    setMessage(
      "Student has been flagged for follow-up."
    );
  } catch (err) {
    console.error("FLAG ERROR:", err);

    setError(
      err.response?.data?.detail ||
        "Unable to flag student."
    );
  }
};

  const handleEndorse = async () => {
    setMessage("");
    setError("");

    try {
      await api.post(
        `/teacher/endorse-path/${studentUsername}`
      );

      setMessage(
        "Career path endorsed successfully."
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to endorse career path."
      );
    }
  };

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading guidance...
        </p>
      </div>
    );
  }

  if (error && !student) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">
          Career Guidance
        </h1>

        <p className="mt-3 text-red-600">{error}</p>
      </div>
    );
  }

  const result = student?.latest_result;

  return (
    <div>
      <button
        type="button"
        onClick={() =>
          navigate(
            `/teacher/student/${studentUsername}`
          )
        }
        className="mb-5 text-sm font-semibold text-violet-600"
      >
        ← Back to Student Progress
      </button>

      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          The Command Center
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Career Guidance
        </h1>

        <p className="mt-3 text-slate-500">
          Supporting {studentUsername}'s career journey.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-2xl bg-red-50 p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      {message && (
        <div className="mb-6 rounded-2xl bg-green-50 p-4 text-sm text-green-700">
          {message}
        </div>
      )}

      {result ? (
        <>
          <div className="rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
              CURRENT DIRECTION
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

          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            {(result.top_3_recommendations || []).map(
              (career, index) => (
                <div
                  key={`${career.career_field}-${career.rank}`}
                  className="rounded-3xl bg-white p-7 shadow-sm"
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

          <div className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
              TEACHER ACTIONS
            </p>

            <h2 className="mt-2 text-2xl font-bold text-slate-900">
              Support this student's direction
            </h2>

            <p className="mt-3 text-slate-500">
              These actions record teacher observations around the current
              assessment result.
            </p>

            <div className="mt-6 flex flex-wrap gap-4">
              <button
                type="button"
                onClick={handleFlag}
                className="rounded-xl border border-amber-300 bg-amber-50 px-5 py-3 font-semibold text-amber-700 transition hover:bg-amber-100"
              >
                Flag for Follow-up
              </button>

              <button
                type="button"
                onClick={handleEndorse}
                className="rounded-xl bg-violet-600 px-5 py-3 font-semibold text-white transition hover:bg-violet-700"
              >
                Endorse Career Path
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="rounded-3xl bg-white p-8 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900">
            Assessment not completed
          </h2>

          <p className="mt-3 text-slate-500">
            There is currently no assessment result to guide career
            recommendations.
          </p>

          <button
            type="button"
            onClick={handleFlag}
            className="mt-6 rounded-xl border border-amber-300 bg-amber-50 px-5 py-3 font-semibold text-amber-700"
          >
            Flag for Follow-up
          </button>
        </div>
      )}

      <div className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          TEACHER CONTEXT
        </p>

        <h2 className="mt-2 text-2xl font-bold text-slate-900">
          Add Academic & Activity Context
        </h2>

        <p className="mt-3 text-sm text-slate-500">
          Academic grades and extracurricular observations are stored as
          additional teacher context.
        </p>

        <form
          onSubmit={handleContextSubmit}
          className="mt-6"
        >
          <label className="text-sm font-semibold text-slate-700">
            Academic Grades
          </label>

          <input
            type="text"
            value={grades}
            onChange={(e) => setGrades(e.target.value)}
            className="mt-3 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none focus:border-violet-500"
            placeholder='Example: {"Math":85,"Science":90}'
          />

          <label className="mt-6 block text-sm font-semibold text-slate-700">
            Extracurricular / Academic Observation
          </label>

          <textarea
            value={extracurricularNote}
            onChange={(e) =>
              setExtracurricularNote(e.target.value)
            }
            rows={6}
            className="mt-3 w-full rounded-2xl border border-slate-300 px-4 py-4 text-slate-900 outline-none focus:border-violet-500"
            placeholder="Describe achievements, activities, leadership, interests, or other useful observations."
          />

          <button
            type="submit"
            disabled={saving}
            className="mt-6 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white transition hover:bg-violet-700 disabled:opacity-60"
          >
            {saving ? "Saving..." : "Save Teacher Context"}
          </button>
        </form>
      </div>

      <div className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          PREVIOUS CONTEXT
        </p>

        <h2 className="mt-2 text-2xl font-bold text-slate-900">
          Teacher Observations
        </h2>

        {context.length === 0 ? (
          <p className="mt-5 text-sm text-slate-500">
            No teacher context has been submitted yet.
          </p>
        ) : (
          <div className="mt-6 space-y-4">
            {context.map((item) => (
              <div
                key={String(item.id)}
                className="rounded-2xl bg-slate-50 p-5"
              >
                {item.academic_grades && (
                  <p className="text-sm text-slate-700">
                    <span className="font-semibold">
                      Grades:
                    </span>{" "}
                    {JSON.stringify(item.academic_grades)}
                  </p>
                )}

                {item.extracurricular_note && (
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    {item.extracurricular_note}
                  </p>
                )}

                <p className="mt-3 text-xs text-slate-400">
                  {new Date(
                    item.submitted_at
                  ).toLocaleString("en-IN")}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default TeacherGuidance;