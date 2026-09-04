import { Navigate } from "react-router-dom";

function ProtectedRoute({ children, allowedRoles }) {
  const token = localStorage.getItem("access_token");
  const role = localStorage.getItem("role");

  if (!token || !role) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(role)) {
    const homeRoutes = {
      student: "/student/home",
      parent: "/parent/home",
      teacher: "/teacher/home",
    };

    return <Navigate to={homeRoutes[role] || "/login"} replace />;
  }

  return children;
}

export default ProtectedRoute;