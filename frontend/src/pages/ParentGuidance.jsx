
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

function ParentGuidance() {
  const navigate = useNavigate();
  const { studentUsername } = useParams();

  const [student, setStudent] = useState(null);
  const [context, setContext] = useState(null);
  const [guidance, setGuidance] = useState(null);

  const [question, setQuestion] = useState(
    "How can I support my child in exploring suitable career options?"
  );

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const studentResponse = await api.get(
          `/parent/child/${studentUsername}`
        );

        const studentData = studentResponse.data;
        setStudent(studentData);

        const studentId = studentData.student?.id;

        if (!studentId) {
          throw new Error(
            "Student ID was not returned by the parent API."
          );
        }

        const guidanceResponse = await api.get(
          `/guidance/${studentId}/context`
        );

        setContext(guidanceResponse.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            err.message ||
            "Unable to load parent guidance."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentUsername]);

  const handleGenerate = async (e) => {
    e.preventDefault();

    setGenerating(true);
    setError("");
    setMessage("");

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
            "How can I support my child in exploring suitable career options?",
        }
      );

      setGuidance(response.data.guidance);
      setMessage("Parent guidance generated successfully.");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to generate parent guidance."
      );
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading parent guidance...
        </p>
      </div>
    );
  }

  if (error && !context) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">
          Career Guidance
        </h1>

        <p className="mt-3 text-red-600">{error}</p>
      </div>
    );
  }

  const mlTop3 = context?.ml_profile?.top_3 || [];
  const interest =
    context?.guidance_context?.student_interest;

  return (
    <div className="space-y-8">
      <button
        type="button"
        onClick={() => navigate("/parent/home")}
        className="text-sm font-semibold text-violet-600"
      >
        ← Back to Parent Home
      </button>

      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Parent Guide
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Career Guidance
        </h1>

        <p className="mt-3 text-slate-500">
          Supporting {studentUsername}'s career exploration.
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

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Assessment Profile
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-900">
            Current ML Top 3
          </h2>

          <div className="mt-5 space-y-3">
            {mlTop3.map((career) => (
              <div
                key={`${career.career_field}-${career.rank}`}
                className="rounded-2xl bg-slate-50 p-4"
              >
                <div className="flex items-center justify-between gap-4">
                  <p className="font-semibold text-slate-900">
                    {career.rank}. {career.career_field}
                  </p>

                  <span className="font-bold text-violet-600">
                    {career.match_score}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Student Preference
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-900">
            Current Interest
          </h2>

          <div className="mt-5 rounded-2xl bg-violet-50 p-5">
            <p className="text-xl font-bold text-violet-700">
              {interest || "No current interest recorded"}
            </p>

            <p className="mt-2 text-sm leading-6 text-slate-600">
              A stated interest is exploratory and does not
              replace the student's assessment-derived profile.
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Guidance Assistant
        </p>

        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          Ask About Your Child's Career Path
        </h2>

        <form onSubmit={handleGenerate} className="mt-6">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
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
              Parent Guidance
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
                Profile Interpretation
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                {guidance.ml_top_3_interpretation}
              </p>
            </div>

            <div className="rounded-3xl bg-white p-7 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">
                Supporting the Student
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                {guidance.stated_interest_guidance}
              </p>
            </div>
          </div>

          <div className="rounded-3xl bg-white p-8 shadow-sm">
            <h3 className="text-2xl font-bold text-slate-900">
              Education Feasibility
            </h3>

            <p className="mt-4 leading-7 text-slate-600">
              {guidance.education_feasibility}
            </p>
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
              Practical Next Steps
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
    </div>
  );
}

export default ParentGuidance;
