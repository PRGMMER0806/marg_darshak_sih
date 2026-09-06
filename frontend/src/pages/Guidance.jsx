import { useEffect, useState } from "react";
import api from "../services/api";

function Guidance() {
  const [context, setContext] = useState(null);
  const [question, setQuestion] = useState("");
  const [guidance, setGuidance] = useState(null);

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const studentId = localStorage.getItem("user_id");

  useEffect(() => {
    const fetchContext = async () => {
      if (!studentId) {
        setError("Student ID not found. Please log in again.");
        setLoading(false);
        return;
      }

      try {
        const response = await api.get(
          `/guidance/${studentId}/context`
        );

        setContext(response.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load your guidance context."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchContext();
  }, [studentId]);

  const handleGenerate = async (e) => {
    e.preventDefault();

    if (!studentId) {
      setError("Student ID not found. Please log in again.");
      return;
    }

    setGenerating(true);
    setError("");
    setMessage("");

    try {
      const response = await api.post(
        `/guidance/${studentId}/generate`,
        {
          question:
            question.trim() ||
            "Provide guidance based on my current career profile.",
        }
      );

      setGuidance(response.data.guidance);
      setMessage("Guidance generated successfully.");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to generate guidance right now."
      );
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading your guidance profile...
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

        <p className="mt-3 text-red-600">
          {error}
        </p>
      </div>
    );
  }

  const assessment = context?.assessment;
  const mlProfile = context?.ml_profile;
  const guidanceContext = context?.guidance_context;

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Your Guide
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Career Guidance
        </h1>

        <p className="mt-3 max-w-3xl text-slate-500">
          Explore your assessment profile, current interests, and
          practical next steps without locking yourself into one career.
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

      {assessment && (
        <div className="rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
            Assessment Profile
          </p>

          <h2 className="mt-3 text-3xl font-bold">
            {mlProfile?.career_field || "Career Profile"}
          </h2>

          <p className="mt-3 text-violet-100">
            Assessment score: {assessment.score}%
          </p>

          {assessment.persona?.name && (
            <p className="mt-2 text-violet-100">
              Persona: {assessment.persona.name}
            </p>
          )}

          {assessment.summary && (
            <p className="mt-5 max-w-4xl leading-7 text-violet-100">
              {assessment.summary}
            </p>
          )}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            ML Top 3
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-900">
            Your Current Directions
          </h2>

          <div className="mt-6 space-y-4">
            {(mlProfile?.top_3 || []).map((career) => (
              <div
                key={`${career.career_field}-${career.rank}`}
                className="rounded-2xl bg-slate-50 p-5"
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs font-bold uppercase text-violet-600">
                      Rank {career.rank}
                    </p>

                    <h3 className="mt-1 font-bold text-slate-900">
                      {career.career_field}
                    </h3>
                  </div>

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
            Current Interest
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-900">
            What You Want to Explore
          </h2>

          <div className="mt-5 rounded-2xl bg-violet-50 p-5">
            <p className="text-sm text-slate-500">
              Stated interest
            </p>

            <p className="mt-2 text-xl font-bold text-violet-700">
              {guidanceContext?.student_interest ||
                "No current interest recorded"}
            </p>
          </div>

          {guidanceContext?.interest_history?.length > 0 && (
            <div className="mt-5">
              <p className="text-sm font-semibold text-slate-700">
                Interest history
              </p>

              <div className="mt-3 space-y-2">
                {guidanceContext.interest_history
                  .slice(0, 5)
                  .map((item, index) => (
                    <div
                      key={`${item.interest}-${index}`}
                      className="rounded-xl border border-slate-200 p-3"
                    >
                      <p className="text-sm font-medium text-slate-800">
                        {item.interest}
                      </p>
                      <p className="mt-1 text-xs text-slate-400">
                        {new Date(
                          item.stated_at
                        ).toLocaleString("en-IN")}
                      </p>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Guidance Assistant
        </p>

        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          Ask Your Career Guide
        </h2>

        <p className="mt-3 max-w-3xl text-slate-500">
          Ask about your career directions, your interests, subjects,
          skills, pathways, or what you should explore next.
        </p>

        <form onSubmit={handleGenerate} className="mt-6">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={5}
            className="w-full rounded-2xl border border-slate-300 px-4 py-4 text-slate-900 outline-none focus:border-violet-500"
            placeholder="Example: I am interested in software engineering. What should I explore next?"
          />

          <button
            type="submit"
            disabled={generating}
            className="mt-4 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {generating
              ? "Generating guidance..."
              : "Ask Guidance Agent"}
          </button>
        </form>
      </div>

      {guidance && (
        <div className="space-y-6">
          <div className="rounded-3xl bg-white p-8 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
              Guidance Result
            </p>

            <h2 className="mt-2 text-3xl font-bold text-slate-900">
              {guidance.title}
            </h2>

            <div className="mt-5 rounded-2xl bg-violet-50 p-5">
              <p className="text-xs font-bold uppercase text-violet-600">
                Case
              </p>

              <p className="mt-1 font-semibold text-slate-900">
                {guidance.case}
              </p>
            </div>

            <p className="mt-6 leading-7 text-slate-600">
              {guidance.student_summary}
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-3xl bg-white p-7 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">
                What Your Profile Says
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                {guidance.case_explanation}
              </p>

              <div className="mt-6">
                <p className="text-sm font-semibold text-slate-700">
                  ML interpretation
                </p>

                <p className="mt-2 leading-7 text-slate-600">
                  {guidance.ml_top_3_interpretation}
                </p>
              </div>
            </div>

            <div className="rounded-3xl bg-white p-7 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">
                Your Interest
              </h3>

              <p className="mt-4 leading-7 text-slate-600">
                {guidance.stated_interest_guidance}
              </p>

              <div className="mt-6">
                <p className="text-sm font-semibold text-slate-700">
                  Education feasibility
                </p>

                <p className="mt-2 leading-7 text-slate-600">
                  {guidance.education_feasibility}
                </p>
              </div>
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

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="rounded-3xl bg-white p-7 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">
                Strongest Current Pathway
              </h3>

              <p className="mt-4 text-sm leading-6 text-slate-600">
                {guidance.strongest_current_pathway}
              </p>
            </div>

            <div className="rounded-3xl bg-white p-7 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">
                Next Steps
              </h3>

              <div className="mt-4 space-y-3">
                {(guidance.immediate_next_steps || []).map(
                  (step, index) => (
                    <div
                      key={index}
                      className="rounded-xl bg-slate-50 p-3 text-sm leading-6 text-slate-600"
                    >
                      {index + 1}. {step}
                    </div>
                  )
                )}
              </div>
            </div>

            <div className="rounded-3xl bg-white p-7 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">
                Questions to Explore
              </h3>

              <div className="mt-4 space-y-3">
                {(guidance.questions_to_explore || []).map(
                  (item, index) => (
                    <div
                      key={index}
                      className="rounded-xl bg-slate-50 p-3 text-sm leading-6 text-slate-600"
                    >
                      {item}
                    </div>
                  )
                )}
              </div>
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

export default Guidance;