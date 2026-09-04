import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import StudentHome from "./pages/StudentHome";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./layouts/AppLayout";
import Assessment from "./pages/Assessment";
import StudentDashboard from "./pages/StudentDashboard";
import CareerPath from "./pages/CareerPath";
import Guidance from "./pages/Guidance";
import ParentHome from "./pages/ParentHome";
import ParentProgress from "./pages/ParentProgress";
import ParentCareerPath from "./pages/ParentCareerPath";
import ParentContext from "./pages/ParentContext";
import ParentGuidance from "./pages/ParentGuidance";
import ParentNotifications from "./pages/ParentNotifications";
import TeacherHome from "./pages/TeacherHome";
import TeacherDashboard from "./pages/TeacherDashboard";
import TeacherStudentProgress from "./pages/TeacherStudentProgress";
import TeacherGuidance from "./pages/TeacherGuidance";
import TeacherNotAppeared from "./pages/TeacherNotAppeared";
import TeacherNotifications from "./pages/TeacherNotifications";
import StudentNotifications from "./pages/StudentNotifications";

function RoleHome({ role }) {
  return (
    <AppLayout>
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-3xl font-bold text-slate-900">
          {role} Home
        </h1>

        <p className="mt-2 text-slate-500">
          Your application dashboard will be built here.
        </p>
      </div>
    </AppLayout>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/student/home"
          element={
            <ProtectedRoute allowedRoles={["student"]}>
              <AppLayout>
                <StudentHome />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route
  path="/student/assessment"
  element={
    <ProtectedRoute allowedRoles={["student"]}>
      <AppLayout>
        <Assessment />
      </AppLayout>
    </ProtectedRoute>
  }
/>

        <Route
  path="/parent/home"
  element={
    <ProtectedRoute allowedRoles={["parent"]}>
      <AppLayout>
        <ParentHome />
      </AppLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/parent/progress/:studentUsername"
  element={
    <ProtectedRoute allowedRoles={["parent"]}>
      <AppLayout>
        <ParentProgress />
      </AppLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/parent/career-path/:studentUsername"
  element={
    <ProtectedRoute allowedRoles={["parent"]}>
      <AppLayout>
        <ParentCareerPath />
      </AppLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/parent/guidance/:studentUsername"
  element={
    <ProtectedRoute allowedRoles={["parent"]}>
      <AppLayout>
        <ParentGuidance />
      </AppLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/parent/notifications"
  element={
    <ProtectedRoute allowedRoles={["parent"]}>
      <AppLayout>
        <ParentNotifications />
      </AppLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/parent/context/:studentUsername"
  element={
    <ProtectedRoute allowedRoles={["parent"]}>
      <AppLayout>
        <ParentContext />
      </AppLayout>
    </ProtectedRoute>
  }
/>

       <Route
  path="/teacher/home"
  element={
    <ProtectedRoute allowedRoles={["teacher"]}>
      <AppLayout>
        <TeacherHome />
      </AppLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/teacher/dashboard"
  element={
    <ProtectedRoute allowedRoles={["teacher"]}>
      <AppLayout>
        <TeacherDashboard />
      </AppLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/teacher/student/:studentUsername"
  element={
    <ProtectedRoute allowedRoles={["teacher"]}>
      <AppLayout>
        <TeacherStudentProgress />
      </AppLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/teacher/guidance/:studentUsername"
  element={
    <ProtectedRoute allowedRoles={["teacher"]}>
      <AppLayout>
        <TeacherGuidance />
      </AppLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/teacher/not-appeared"
  element={
    <ProtectedRoute allowedRoles={["teacher"]}>
      <AppLayout>
        <TeacherNotAppeared />
      </AppLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/teacher/notifications"
  element={
    <ProtectedRoute allowedRoles={["teacher"]}>
      <AppLayout>
        <TeacherNotifications />
      </AppLayout>
    </ProtectedRoute>
  }
/>

        <Route
  path="/student/dashboard"
  element={
    <ProtectedRoute allowedRoles={["student"]}>
      <AppLayout>
        <StudentDashboard />
      </AppLayout>
    </ProtectedRoute>
  }
/>

      
      <Route
  path="/student/career-path"
  element={
    <ProtectedRoute allowedRoles={["student"]}>
      <AppLayout>
        <CareerPath />
      </AppLayout>
    </ProtectedRoute>
  }
/>

      <Route
  path="/student/guidance"
  element={
    <ProtectedRoute allowedRoles={["student"]}>
      <AppLayout>
        <Guidance />
      </AppLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/student/notifications"
  element={
    <ProtectedRoute allowedRoles={["student"]}>
      <AppLayout>
        <StudentNotifications />
      </AppLayout>
    </ProtectedRoute>
  }
/>

      </Routes>
    </BrowserRouter>
  );
}

export default App;