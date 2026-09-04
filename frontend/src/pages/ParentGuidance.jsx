import { useNavigate, useParams } from "react-router-dom";

function ParentGuidance() {
  const navigate = useNavigate();
  const { studentUsername } = useParams();

  return (
    <div>
      <button
        type="button"
        onClick={() => navigate("/parent/home")}
        className="mb-5 text-sm font-semibold text-violet-600"
      >
        ← Back to Parent Home
      </button>

      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          The Guide
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Career Guidance
        </h1>

        <p className="mt-3 max-w-3xl text-slate-500">
          Guidance for {studentUsername} will eventually combine assessment
          results with relevant human context.
        </p>
      </div>

      <div className="rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
          Guidance Foundation
        </p>

        <h2 className="mt-3 text-3xl font-bold">
          Understand. Support. Explore.
        </h2>

        <p className="mt-4 max-w-3xl leading-7 text-violet-100">
          Parents will be able to understand recommended career directions,
          explore suitable opportunities, and support their child's
          development.
        </p>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-3">
        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <h3 className="text-xl font-bold text-slate-900">
            Understand
          </h3>

          <p className="mt-3 text-sm leading-6 text-slate-500">
            Understand the student's assessment profile and recommended
            directions.
          </p>
        </div>

        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <h3 className="text-xl font-bold text-slate-900">
            Support
          </h3>

          <p className="mt-3 text-sm leading-6 text-slate-500">
            Provide useful behavioral and interest observations through the
            Parent Context system.
          </p>
        </div>

        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <h3 className="text-xl font-bold text-slate-900">
            Explore
          </h3>

          <p className="mt-3 text-sm leading-6 text-slate-500">
            Explore the student's recommended career paths without treating
            any single recommendation as a fixed decision.
          </p>
        </div>
      </div>

      <div className="mt-8 rounded-3xl bg-white p-8 shadow-sm">
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-700">
          AI GUIDANCE AGENT COMING LATER
        </span>

        <h2 className="mt-5 text-2xl font-bold text-slate-900">
          Personalized Guidance
        </h2>

        <p className="mt-3 max-w-3xl leading-7 text-slate-500">
          The actual AI Guidance Agent will be integrated after the complete
          student, parent, and teacher UI/backend systems are finished.
        </p>
      </div>
    </div>
  );
}

export default ParentGuidance;