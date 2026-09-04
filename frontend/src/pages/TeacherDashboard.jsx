import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function TeacherDashboard() {
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await api.get("/teacher/dashboard");
        setData(response.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load class dashboard."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading class dashboard...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">
          Class Dashboard
        </h1>

        <p className="mt-3 text-red-600">{error}</p>
      </div>
    );
  }

  const statistics = data.statistics || {};
  const students = data.students || [];

  return (
    <div>
      <button
        type="button"
        onClick={() => navigate("/teacher/home")}
        className="mb-5 text-sm font-semibold text-violet-600"
      >
        ← Back to Teacher Home
      </button>

      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          The Command Center
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Class Dashboard
        </h1>

        <p className="mt-3 text-slate-500">
          {data.class_name || "Class"} · {data.school_id || "School"}
        </p>
      </div>

      <div className="mb-8 grid gap-6 md:grid-cols-3">
        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            TOTAL STUDENTS
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {statistics.total_students || 0}
          </h2>
        </div>

        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            COMPLETED
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {statistics.completed_assessment || 0}
          </h2>
        </div>

        <div className="rounded-3xl bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold text-violet-600">
            NOT APPEARED
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {statistics.not_appeared || 0}
          </h2>
        </div>
      </div>

      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          STUDENTS
        </p>

        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          Student Overview
        </h2>

        {students.length === 0 ? (
          <div className="mt-6 rounded-2xl bg-slate-50 p-6 text-center">
            <p className="font-semibold text-slate-900">
              No students found
            </p>

            <p className="mt-2 text-sm text-slate-500">
              There are currently no students in this class.
            </p>
          </div>
        ) : (
          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-[700px] text-left">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="pb-4 text-sm text-slate-500">
                    Student
                  </th>

                  <th className="pb-4 text-sm text-slate-500">
                    Score
                  </th>

                  <th className="pb-4 text-sm text-slate-500">
                    Career Direction
                  </th>

                  <th className="pb-4 text-sm text-slate-500">
                    Status
                  </th>

                  <th className="pb-4 text-sm text-slate-500">
                    Action
                  </th>
                </tr>
              </thead>

              <tbody>
                {students.map((student) => (
                  <tr
                    key={student.student_id}
                    className="border-b border-slate-100"
                  >
                    <td className="py-5 font-semibold text-slate-900">
                      {student.student_username}
                    </td>

                    <td className="py-5 text-sm text-slate-700">
                      {student.latest_score != null
                        ? `${student.latest_score}%`
                        : "—"}
                    </td>

                    <td className="py-5 text-sm text-slate-700">
                      {student.career_field || "Not assessed"}
                    </td>

                    <td className="py-5">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-bold ${
                          student.has_completed_assessment
                            ? "bg-green-100 text-green-700"
                            : "bg-amber-100 text-amber-700"
                        }`}
                      >
                        {student.has_completed_assessment
                          ? "ASSESSED"
                          : "NOT APPEARED"}
                      </span>
                    </td>

                    <td className="py-5">
                      <button
                        type="button"
                        onClick={() =>
                          navigate(
                            `/teacher/student/${student.student_username}`
                          )
                        }
                        className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-violet-700"
                      >
                        View Student
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default TeacherDashboard;