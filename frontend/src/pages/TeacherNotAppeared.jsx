import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function TeacherNotAppeared() {
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        const response = await api.get("/teacher/not-appeared");
        setData(response.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load students."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchStudents();
  }, []);

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-slate-500">
          Loading students...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  const students = data.not_appeared || [];

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
          Follow-up
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Students Not Appeared
        </h1>

        <p className="mt-3 text-slate-500">
          {data.class_name} · Students who have not completed an assessment.
        </p>
      </div>

      {students.length === 0 ? (
        <div className="rounded-3xl bg-white p-8 text-center shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900">
            Everyone is up to date
          </h2>

          <p className="mt-3 text-slate-500">
            All students in this class have completed an assessment.
          </p>
        </div>
      ) : (
        <div className="rounded-3xl bg-white p-8 shadow-sm">
          <div className="space-y-4">
            {students.map((student) => (
              <div
                key={student.student_id}
                className="flex flex-col gap-4 rounded-2xl bg-slate-50 p-5 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-bold text-slate-900">
                    {student.student_username}
                  </p>

                  <p className="mt-1 text-sm text-amber-600">
                    Assessment not completed
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      `/teacher/student/${student.student_username}`
                    )
                  }
                  className="rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white"
                >
                  View Student
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default TeacherNotAppeared;