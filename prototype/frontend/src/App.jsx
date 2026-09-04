import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";

import StudentHome from "./pages/StudentHome";
import ParentHome from "./pages/ParentHome";
import TeacherHome from "./pages/TeacherHome";

import Assessment from "./pages/Assessment";
import StudentDashboard from "./pages/StudentDashboard";
import CareerPath from "./pages/CareerPath";

import ParentChildDashboard from "./pages/ParentChildDashboard";
import TeacherStudentDashboard from "./pages/TeacherStudentDashboard";

import Messages from "./pages/Messages";
import Notifications from "./pages/Notifications";

import ProtectedRoute from "./components/ProtectedRoute";
import AppShell from "./components/AppShell";


function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Public routes */}

        <Route
          path="/"
          element={<Home />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/register"
          element={<Register />}
        />


        {/* Student */}

        <Route
          path="/student"
          element={
            <ProtectedRoute allowedRole="student">
              <AppShell>
                <StudentHome />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/aptitude"
          element={
            <ProtectedRoute allowedRole="student">
              <AppShell>
                <Assessment />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/student/dashboard"
          element={
            <ProtectedRoute allowedRole="student">
              <AppShell>
                <StudentDashboard />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/student/career-path"
          element={
            <ProtectedRoute allowedRole="student">
              <AppShell>
                <CareerPath />
              </AppShell>
            </ProtectedRoute>
          }
        />


        {/* Parent */}

        <Route
          path="/parent"
          element={
            <ProtectedRoute allowedRole="parent">
              <AppShell>
                <ParentHome />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/parent/child/:studentUsername"
          element={
            <ProtectedRoute allowedRole="parent">
              <AppShell>
                <ParentChildDashboard />
              </AppShell>
            </ProtectedRoute>
          }
        />


        {/* Teacher */}

        <Route
          path="/teacher"
          element={
            <ProtectedRoute allowedRole="teacher">
              <AppShell>
                <TeacherHome />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/teacher/student/:studentUsername"
          element={
            <ProtectedRoute allowedRole="teacher">
              <AppShell>
                <TeacherStudentDashboard />
              </AppShell>
            </ProtectedRoute>
          }
        />


        {/* Shared */}

        <Route
          path="/messages"
          element={
            <ProtectedRoute
              allowedRole={[
                "student",
                "parent",
                "teacher",
              ]}
            >
              <AppShell>
                <Messages />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/notifications"
          element={
            <ProtectedRoute
              allowedRole={[
                "student",
                "parent",
                "teacher",
              ]}
            >
              <AppShell>
                <Notifications />
              </AppShell>
            </ProtectedRoute>
          }
        />


        {/* Unknown route */}

        <Route
          path="*"
          element={<Home />}
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;

