import { useNavigate } from "react-router-dom";

function StudentHome() {
  const username = localStorage.getItem("username");
  const navigate = useNavigate();

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Your Journey
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Welcome, {username || "Student"}.
        </h1>

        <p className="mt-3 max-w-2xl text-slate-500">
          Your career journey starts with understanding yourself. Discover
          your strengths, explore possibilities, and build your path step by
          step.
        </p>
      </div>

      <div className="mb-8 grid gap-6 md:grid-cols-3">
        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            JOURNEY
          </p>

          <h2 className="mt-3 text-2xl font-bold text-slate-900">
            Just Getting Started
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Complete your first assessment to begin discovering your career
            direction.
          </p>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            PROGRESS
          </p>

          <h2 className="mt-3 text-2xl font-bold text-slate-900">
            0%
          </h2>

          <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full w-0 rounded-full bg-violet-600" />
          </div>

          <p className="mt-3 text-sm text-slate-500">
            Your progress will appear here as you complete your journey.
          </p>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            DISCOVERY
          </p>

          <h2 className="mt-3 text-2xl font-bold text-slate-900">
            3 Career Paths
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Your assessment results will unlock career paths matched to your
            strengths and interests.
          </p>
        </div>
      </div>

      <div className="rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
          Next Mission
        </p>

        <h2 className="mt-3 text-3xl font-bold">
          Discover Your Strengths
        </h2>

        <p className="mt-3 max-w-2xl leading-7 text-violet-100">
          Take the aptitude and RIASEC assessment to understand your interests,
          abilities, and career preferences.
        </p>

        <button
  type="button"
  onClick={() => navigate("/student/assessment")}
  className="mt-6 rounded-xl bg-white px-6 py-3 font-semibold text-violet-700 transition hover:bg-violet-50"
>
  Start Assessment
</button>
      </div>
    </div>
  );
}

export default StudentHome;