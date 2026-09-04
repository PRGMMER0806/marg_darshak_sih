import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { logout } from "../services/auth";

function AppLayout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  const username = localStorage.getItem("username");
  const role = localStorage.getItem("role");

  const [assessmentLocked, setAssessmentLocked] = useState(
    () => localStorage.getItem("assessment_locked") === "true"
  );

  useEffect(() => {
    const handleAssessmentLock = () => {
      setAssessmentLocked(
        localStorage.getItem("assessment_locked") === "true"
      );
    };

    window.addEventListener(
      "assessment-lock-changed",
      handleAssessmentLock
    );

    return () => {
      window.removeEventListener(
        "assessment-lock-changed",
        handleAssessmentLock
      );
    };
  }, []);

  const navigation = {
    student: [
  { label: "Home", path: "/student/home" },
  { label: "Assessment", path: "/student/assessment" },
  { label: "Dashboard", path: "/student/dashboard" },
  { label: "Career Path", path: "/student/career-path" },
  { label: "Guidance", path: "/student/guidance" },
  { label: "Notifications", path: "/student/notifications" },
],
    parent: [
  { label: "Home", path: "/parent/home" },
  { label: "Notifications", path: "/parent/notifications" },
],
    teacher: [
  { label: "Home", path: "/teacher/home" },
  { label: "Class Dashboard", path: "/teacher/dashboard" },
  { label: "Not Appeared", path: "/teacher/not-appeared" },
  { label: "Notifications", path: "/teacher/notifications" },
],
  };

  const roleNames = {
    student: "Student",
    parent: "Parent",
    teacher: "Teacher",
  };

  const handleLogout = () => {
    if (role === "student" && assessmentLocked) {
      return;
    }

    logout();
    navigate("/login");
  };

  const handleNavigation = (path) => {
    if (
      role === "student" &&
      assessmentLocked &&
      path !== "/student/assessment"
    ) {
      return;
    }

    navigate(path);
  };

  const isNavigationLocked =
    role === "student" && assessmentLocked;

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-sm font-bold tracking-wide text-violet-600">
              CAREERPATH
            </p>

            <p className="text-xs text-slate-500">
              {roleNames[role] || "User"} Portal
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-semibold text-slate-900">
                {username}
              </p>

              <p className="text-xs capitalize text-slate-500">
                {role}
              </p>
            </div>

            <button
              onClick={handleLogout}
              disabled={isNavigationLocked}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl">
        <aside className="w-60 shrink-0 py-6 pr-6">
          <nav className="space-y-2">
            {navigation[role]?.map((item) => {
              const isLocked =
                role === "student" &&
                assessmentLocked &&
                item.path !== "/student/assessment";

              const isActive =
                location.pathname === item.path;

              return (
                <button
                  key={item.path}
                  onClick={() => handleNavigation(item.path)}
                  disabled={isLocked}
                  className={`w-full rounded-xl px-4 py-3 text-left text-sm font-medium transition ${
                    isLocked
                      ? "cursor-not-allowed text-slate-300"
                      : isActive
                      ? "bg-violet-50 text-violet-700"
                      : "text-slate-600 hover:bg-white hover:text-violet-600 hover:shadow-sm"
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {isNavigationLocked && (
            <div className="mt-6 rounded-2xl bg-amber-50 p-4">
              <p className="text-xs font-semibold text-amber-700">
                ASSESSMENT IN PROGRESS
              </p>

              <p className="mt-2 text-xs leading-5 text-amber-600">
                Complete your assessment before accessing other sections.
              </p>
            </div>
          )}
        </aside>

        <main className="min-w-0 flex-1 py-8">
          {children}
        </main>
      </div>
    </div>
  );
}

export default AppLayout;