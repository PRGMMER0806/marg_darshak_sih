import { useEffect, useState } from "react";
import api from "../services/api";

function CareerPath() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchCareerPath = async () => {
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
            "Unable to load your career path."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchCareerPath();
  }, []);

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading your career path...
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

        <p className="mt-3 text-red-600">
          {error}
        </p>
      </div>
    );
  }

  const result = dashboard.latest_result;
  const careers = result.top_3_recommendations || [];
  const persona = result.persona;

  const riasecNames = {
    R: "Realistic",
    I: "Investigative",
    A: "Artistic",
    S: "Social",
    E: "Enterprising",
    C: "Conventional",
  };

  const aptitude = result.statistical_evaluation.aptitude;
  const riasec = result.statistical_evaluation.riasec;

  const strongestAptitude = Object.entries(aptitude)
    .filter(([, value]) => value !== null && value !== undefined)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2);

  const strongestRiasec = Object.entries(riasec)
    .filter(([, value]) => value !== null && value !== undefined)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2);

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Your Journey
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Your Career Path
        </h1>

        <p className="mt-3 max-w-3xl text-slate-500">
          Explore the career directions identified from your assessment
          results and discover where your strengths could take you.
        </p>
      </div>

      <div className="rounded-3xl bg-violet-600 p-8 text-white shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-200">
          Recommended Direction
        </p>

        <h2 className="mt-3 text-3xl font-bold">
          {result.top_career.career_field}
        </h2>

        <div className="mt-5 flex flex-wrap gap-3">
          <span className="rounded-full bg-white/15 px-4 py-2 text-sm font-semibold">
            {result.top_career.match_score}% Match
          </span>

          <span className="rounded-full bg-white/15 px-4 py-2 text-sm font-semibold">
            {persona.name}
          </span>
        </div>

        <p className="mt-5 max-w-3xl leading-7 text-violet-100">
          {result.summary}
        </p>
      </div>

      <div className="mt-10">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Career Discovery
          </p>

          <h2 className="mt-2 text-3xl font-bold text-slate-900">
            Explore Your 3 Paths
          </h2>

          <p className="mt-2 max-w-2xl text-slate-500">
            Your assessment does not limit you to one career. These three
            paths represent your strongest current directions.
          </p>
        </div>

        <div className="space-y-6">
          {careers.map((career, index) => (
            <div
              key={`${career.career_field}-${career.rank}`}
              className={`rounded-3xl bg-white p-8 shadow-sm ${
                index === 0
                  ? "ring-2 ring-violet-500"
                  : ""
              }`}
            >
              <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
                <div className="flex gap-5">
                  <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-violet-50 text-xl font-bold text-violet-700">
                    {index + 1}
                  </div>

                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <p className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                        Career Path {index + 1}
                      </p>

                      {index === 0 && (
                        <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-bold text-violet-700">
                          TOP MATCH
                        </span>
                      )}
                    </div>

                    <h3 className="mt-2 text-2xl font-bold text-slate-900">
                      {career.career_field}
                    </h3>
                  </div>
                </div>

                <div className="min-w-[180px]">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-500">
                      Match
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
                          Math.max(career.confidence_pct || 0, 0),
                          100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-3">
                <div className="rounded-2xl bg-slate-50 p-5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Based On
                  </p>

                  <p className="mt-2 text-sm font-semibold text-slate-800">
                    Aptitude + Interests
                  </p>
                </div>

                <div className="rounded-2xl bg-slate-50 p-5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Your Persona
                  </p>

                  <p className="mt-2 text-sm font-semibold text-slate-800">
                    {persona.name}
                  </p>
                </div>

                <div className="rounded-2xl bg-slate-50 p-5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Current Match
                  </p>

                  <p className="mt-2 text-sm font-semibold text-slate-800">
                    {career.confidence_pct}%
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-10">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Why These Paths Fit You
          </p>

          <h2 className="mt-2 text-3xl font-bold text-slate-900">
            Your Strongest Signals
          </h2>

          <p className="mt-2 max-w-2xl text-slate-500">
            These are the strongest assessment areas currently shaping your
            career recommendations.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-3xl bg-white p-7 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
              Aptitude Strengths
            </p>

            <div className="mt-5 space-y-4">
              {strongestAptitude.map(([skill, value]) => (
                <div
                  key={skill}
                  className="flex items-center justify-between rounded-2xl bg-slate-50 p-4"
                >
                  <span className="font-medium capitalize text-slate-700">
                    {skill}
                  </span>

                  <span className="font-bold text-violet-600">
                    {value}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl bg-white p-7 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
              Interest Strengths
            </p>

            <div className="mt-5 space-y-4">
              {strongestRiasec.map(([trait, value]) => (
                <div
                  key={trait}
                  className="flex items-center justify-between rounded-2xl bg-slate-50 p-4"
                >
                  <span className="font-medium text-slate-700">
                    {riasecNames[trait] || trait}
                  </span>

                  <span className="font-bold text-violet-600">
                    {value}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-10 rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Your Next Steps
        </p>

        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          Turn Discovery Into Direction
        </h2>

        <div className="mt-8 grid gap-6 md:grid-cols-3">
          <div className="rounded-2xl bg-slate-50 p-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 font-bold text-violet-700">
              1
            </div>

            <h3 className="mt-4 text-lg font-bold text-slate-900">
              Explore
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Learn what each career path involves and what kind of work it
              includes.
            </p>
          </div>

          <div className="rounded-2xl bg-slate-50 p-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 font-bold text-violet-700">
              2
            </div>

            <h3 className="mt-4 text-lg font-bold text-slate-900">
              Learn
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Discover the subjects, skills, courses, and opportunities
              connected to your chosen direction.
            </p>
          </div>

          <div className="rounded-2xl bg-slate-50 p-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 font-bold text-violet-700">
              3
            </div>

            <h3 className="mt-4 text-lg font-bold text-slate-900">
              Prepare
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Build a practical plan with guidance and milestones for your
              future career.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CareerPath;