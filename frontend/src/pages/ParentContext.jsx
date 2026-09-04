import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

function ParentContext() {
  const navigate = useNavigate();
  const { studentUsername } = useParams();

  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    setLoading(true);
    setMessage("");
    setError("");

    try {
      await api.post("/parent/context", {
        student_id: studentUsername,
        note,
      });

      setMessage(
        "Your observation has been saved successfully."
      );

      setNote("");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to save your observation."
      );
    } finally {
      setLoading(false);
    }
  };

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
          Parent Perspective
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Share Your Observation
        </h1>

        <p className="mt-3 max-w-3xl text-slate-500">
          Share behavioral or interest observations that may help provide
          additional context around your child's career journey.
        </p>
      </div>

      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold text-slate-700">
          Student
        </p>

        <p className="mt-2 text-xl font-bold text-slate-900">
          {studentUsername}
        </p>

        <form onSubmit={handleSubmit} className="mt-8">
          <label className="text-sm font-semibold text-slate-700">
            Behavioral / Interest Observation
          </label>

          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            required
            rows={7}
            className="mt-3 w-full rounded-2xl border border-slate-300 px-4 py-4 text-slate-900 outline-none focus:border-violet-500"
            placeholder="Example: My child enjoys explaining ideas to others and often spends time writing, designing, or exploring new topics."
          />

          {error && (
            <div className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-600">
              {error}
            </div>
          )}

          {message && (
            <div className="mt-4 rounded-xl bg-green-50 p-4 text-sm text-green-700">
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-6 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white transition hover:bg-violet-700 disabled:opacity-60"
          >
            {loading ? "Saving..." : "Save Observation"}
          </button>
        </form>

        <div className="mt-8 rounded-2xl bg-amber-50 p-5">
          <p className="text-sm font-semibold text-amber-800">
            Important
          </p>

          <p className="mt-2 text-sm leading-6 text-amber-700">
            This observation is stored as parent context. It does not change
            the student's assessment score or ML-generated career result.
          </p>
        </div>
      </div>
    </div>
  );
}

export default ParentContext;