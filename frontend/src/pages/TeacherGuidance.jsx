
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

function TeacherGuidance() {
  const navigate = useNavigate();
  const { studentUsername } = useParams();

  const [student, setStudent] = useState(null);
  const [context, setContext] = useState([]);
  const [guidanceContext, setGuidanceContext] = useState(null);
  const [guidance, setGuidance] = useState(null);

  const [grades, setGrades] = useState("");
  const [extracurricularNote, setExtracurricularNote] =
    useState("");

  const [question, setQuestion] = useState(
    "How can I support this student's career exploration?"
  );

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const fetchData = async () => {
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

      const studentData = studentResponse.data;

      setStudent(studentData);
      setContext(contextResponse.data.contexts || []);

      // Teacher API returns:
      // {
      //   student: {
      //     id: "...",
      //     username: "...",
      //     ...
      //   },
      //   ...
      // }
      const studentId = studentData.student?.id;

      if (!studentId) {
        throw new Error(
          "Student ID was not returned by the teacher API."
        );
      }

      const guidanceResponse = await api.get(
        `/guidance/${studentId}/context`
      );

      setGuidanceContext(guidanceResponse.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to load career guidance."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
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

      await fetchData();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to save teacher context."
      );
    } finally {
      setSaving(false);
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();

    setGenerating(true);
    setMessage("");
    setError("");

    try {
      const studentId = student?.student?.id;

      if (!studentId) {
        throw new Error("Student ID is unavailable.");
      }

      const response = await api.post(
        `/guidance/${studentId}/generate`,
        {
          question:
            question.trim() ||
            "How can I support this student's career exploration?",
        }
      );

      setGuidance(response.data.guidance);
      setMessage(
        "Teacher guidance generated successfully."
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to generate teacher guidance."
      );
    } finally {
      setGenerating(false);
    }
  };

  const handleFlag = async () => {
    setMessage("");
    setError("");

    try {
      await api.post(
        `/teacher/flag-followup/${studentUsername}`
      );

      setMessage(
        "Student has been flagged for follow-up."
      );
    } catch (err) {
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

        <p className="mt-3 text-red-600">
          {error}
        </p>
      </div>
    );
  }

  const result = student?.latest_result;
  const mlTop3 =
    guidanceContext?.ml_profile?.top_3 || [];

  const teacherContext =
    guidanceContext?.guidance_context?.teacher_context;

  return (
    <div className="space-y-8">
      <button
        type="button"
        onClick={() =>
          navigate(
            `/teacher/student/${studentUsername}`
          )
        }
        className="text-sm font-semibold text-violet-600"
      >
        ← Back to Student Progress
      </button>

      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Teacher Guide
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Career Guidance
        </h1>

        <p className="mt-3 text-slate-500">
          Supporting {studentUsername}'s career journey.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl bg-red-50 p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      {message && (
        <div className="rounded-2xl bg-green-50 p-4 text-sm text-green-700">
          {message}
        </div>
      )}

      {result && (
        <>
          <div className="rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
              Current Direction
            </p>

            <h2 className="mt-3 text-3xl font-bold">
              {result.top_career?.career_field}
            </h2>

            <p className="mt-3 text-violet-100">
              {result.top_career?.match_score}% match
            </p>

            <p className="mt-5 max-w-3xl leading-7 text-violet-100">
              {result.summary}
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {mlTop3.map((career) => (
              <div
                key={`${career.career_field}-${career.rank}`}
                className="rounded-3xl bg-white p-7 shadow-sm"
              >
                <p className="text-xs font-bold uppercase text-violet-600">
                  Rank {career.rank}
                </p>

                <h3 className="mt-3 text-xl font-bold text-slate-900">
                  {career.career_field}
                </h3>

                <p className="mt-4 text-2xl font-bold text-violet-600">
                  {career.match_score}%
                </p>
              </div>
            ))}
          </div>
        </>
      )}

      {guidanceContext && (
        <div className="rounded-3xl bg-white p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Teacher Context
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-900">
            Context Used by Guidance
          </h2>

          {teacherContext ? (
            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <div className="rounded-2xl bg-slate-50 p-6">
                <p className="text-sm font-semibold text-slate-700">
                  Academic Grades
                </p>

                <pre className="mt-3 overflow-auto rounded-xl bg-white p-4 text-sm text-slate-600">
                  {JSON.stringify(
                    teacherContext.academic_grades || {},
                    null,
                    2
                  )}
                </pre>
              </div>

              <div className="rounded-2xl bg-slate-50 p-6">
                <p className="text-sm font-semibold text-slate-700">
                  Extracurricular Observation
                </p>

                <p className="mt-3 leading-7 text-slate-600">
                  {teacherContext.extracurricular_note ||
                    "No extracurricular observation recorded."}
                </p>
              </div>
            </div>
          ) : (
            <p className="mt-5 text-sm text-slate-500">
              No current teacher context is attached to this
              guidance request.
            </p>
          )}
        </div>
      )}

      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Guidance Assistant
        </p>

        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          Ask About This Student
        </h2>

        <form onSubmit={handleGenerate} className="mt-6">
          <textarea
            value={question}
            onChange={(e) =>
              setQuestion(e.target.value)
            }
            rows={5}
            className="w-full rounded-2xl border border-slate-300 px-4 py-4 text-slate-900 outline-none focus:border-violet-500"
          />

          <button
            type="submit"
            disabled={generating}
            className="mt-4 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white transition hover:bg-violet-700 disabled:opacity-60"
          >
            {generating
              ? "Generating..."
              : "Ask Guidance Agent"}
          </button>
        </form>
      </div>

      {guidance && (
        <div className="space-y-6">
          <div className="rounded-3xl bg-white p-8 shadow-sm">
            <p className="text-sm font-semibold uppercase text-violet-600">
              Teacher Guidance
            </p>

            <h2 className="mt-2 text-3xl font-bold text-slate-900">
              {guidance.title}
            </h2>

            <p className="mt-5 leading-7 text-slate-600">
              {guidance.student_summary}
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-3xl bg-white p-7 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">
                ML Profile
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                {guidance.ml_top_3_interpretation}
              </p>
            </div>

            <div className="rounded-3xl bg-white p-7 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">
                Education Feasibility
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                {guidance.education_feasibility}
              </p>
            </div>
          </div>

          <div className="rounded-3xl bg-white p-8 shadow-sm">
            <h3 className="text-2xl font-bold text-slate-900">
              Pathways to Explore
            </h3>

            <div className="mt-6 grid gap-5 lg:grid-cols-2">
              {(guidance.pathway_guidance || []).map(
                (pathway) => (
                  <div
                    key={pathway.career_field}
                    className="rounded-2xl bg-slate-50 p-6"
                  >
                    <p className="text-xs font-bold uppercase text-violet-600">
                      {pathway.relationship_to_student}
                    </p>

                    <h4 className="mt-2 text-xl font-bold text-slate-900">
                      {pathway.career_field}
                    </h4>

                    <p className="mt-4 text-sm leading-6 text-slate-600">
                      {pathway.why_explore}
                    </p>

                    <p className="mt-4 text-sm leading-6 text-slate-700">
                      {pathway.route_summary}
                    </p>
                  </div>
                )
              )}
            </div>
          </div>

          <div className="rounded-3xl bg-white p-8 shadow-sm">
            <h3 className="text-2xl font-bold text-slate-900">
              Recommended Support
            </h3>

            <div className="mt-5 space-y-3">
              {(guidance.immediate_next_steps || []).map(
                (step, index) => (
                  <div
                    key={index}
                    className="rounded-xl bg-slate-50 p-4 text-sm leading-6 text-slate-600"
                  >
                    {index + 1}. {step}
                  </div>
                )
              )}
            </div>
          </div>

          {guidance.important_caveats?.length > 0 && (
            <div className="rounded-3xl bg-amber-50 p-7">
              <h3 className="text-xl font-bold text-amber-900">
                Important
              </h3>

              <div className="mt-4 space-y-2">
                {guidance.important_caveats.map(
                  (item, index) => (
                    <p
                      key={index}
                      className="text-sm leading-6 text-amber-800"
                    >
                      • {item}
                    </p>
                  )
                )}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          TEACHER ACTIONS
        </p>

        <h2 className="mt-2 text-2xl font-bold text-slate-900">
          Support this student's direction
        </h2>

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

      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          TEACHER CONTEXT
        </p>

        <h2 className="mt-2 text-2xl font-bold text-slate-900">
          Add Academic & Activity Context
        </h2>

        <p className="mt-3 text-sm text-slate-500">
          Academic grades and extracurricular observations are
          stored as additional teacher context.
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
            onChange={(e) =>
              setGrades(e.target.value)
            }
            className="mt-3 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none focus:border-violet-500"
            placeholder='Example: {"Math":85,"Science":90}'
          />

          <label className="mt-6 block text-sm font-semibold text-slate-700">
            Extracurricular / Academic Observation
          </label>

          <textarea
            value={extracurricularNote}
            onChange={(e) =>
              setExtracurricularNote(
                e.target.value
              )
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
            {saving
              ? "Saving..."
              : "Save Teacher Context"}
          </button>
        </form>
      </div>

      <div className="rounded-3xl bg-white p-8 shadow-sm">
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
                    {JSON.stringify(
                      item.academic_grades
                    )}
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

