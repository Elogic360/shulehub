import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/Navbar';
import { Sidebar } from '../components/Sidebar';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { LandingPage } from '../pages/LandingPage';
import { Login } from '../features/auth/Login';
import { RegisterSchool } from '../features/auth/RegisterSchool';
import { ForgotPassword } from '../features/auth/ForgotPassword';
import { ResetPassword } from '../features/auth/ResetPassword';
import { OwnerDashboard } from '../features/owner/OwnerDashboard';
import { AcademicStructure } from '../features/owner/AcademicStructure';
import { StaffManagement } from '../features/owner/StaffManagement';
import { FeeManagement } from '../features/owner/FeeManagement';
import { TeacherDashboard } from '../features/teacher/TeacherDashboard';
import { ClassStudents } from '../features/teacher/ClassStudents';
import { ClassCommunication } from '../features/teacher/ClassCommunication';
import { ClassExaminations } from '../features/teacher/ClassExaminations';
import { ClassMeetings } from '../features/teacher/ClassMeetings';
import { ParentPortal } from '../features/parent/ParentPortal';
import { PlatformAdminDashboard } from '../features/admin/PlatformAdminDashboard';
import { ImportCenter } from '../features/imports/ImportCenter';
import { NectaDashboard } from '../features/necta/NectaDashboard';
import { UssdSimulator } from '../features/ussd/UssdSimulator';

const ProtectedLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl">
          <Breadcrumbs />
          {children}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  const { user, activeRole } = useAuth();

  // Route root intelligently based on role
  const getHomeRoute = () => {
    if (!user) return <Navigate to="/login" replace />;
    if (user.is_superadmin) return <Navigate to="/admin" replace />;
    if (activeRole === 'SCHOOL_OWNER' || activeRole === 'SCHOOL_ADMIN') return <Navigate to="/owner" replace />;
    if (activeRole === 'CLASS_TEACHER') return <Navigate to="/teacher" replace />;
    if (activeRole === 'PARENT') return <Navigate to="/parent" replace />;
    return <Navigate to="/login" replace />;
  };

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/dashboard" element={getHomeRoute()} />
      <Route path="/login" element={!user ? <Login /> : getHomeRoute()} />
      <Route path="/register-school" element={<RegisterSchool />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      {/* Super Admin Routes */}
      <Route path="/admin" element={<ProtectedLayout><PlatformAdminDashboard /></ProtectedLayout>} />
      <Route path="/admin/schools" element={<ProtectedLayout><PlatformAdminDashboard /></ProtectedLayout>} />

      {/* School Owner & Admin Routes */}
      <Route path="/owner" element={<ProtectedLayout><OwnerDashboard /></ProtectedLayout>} />
      <Route path="/owner/academic" element={<ProtectedLayout><AcademicStructure /></ProtectedLayout>} />
      <Route path="/owner/staff" element={<ProtectedLayout><StaffManagement /></ProtectedLayout>} />
      <Route path="/owner/students" element={<ProtectedLayout><ClassStudents /></ProtectedLayout>} />
      <Route path="/owner/communication" element={<ProtectedLayout><ClassCommunication /></ProtectedLayout>} />
      <Route path="/owner/examinations" element={<ProtectedLayout><ClassExaminations /></ProtectedLayout>} />
      <Route path="/owner/fees" element={<ProtectedLayout><FeeManagement /></ProtectedLayout>} />
      <Route path="/owner/meetings" element={<ProtectedLayout><ClassMeetings /></ProtectedLayout>} />

      {/* Class Teacher Routes */}
      <Route path="/teacher" element={<ProtectedLayout><TeacherDashboard /></ProtectedLayout>} />
      <Route path="/teacher/students" element={<ProtectedLayout><ClassStudents /></ProtectedLayout>} />
      <Route path="/teacher/communication" element={<ProtectedLayout><ClassCommunication /></ProtectedLayout>} />
      <Route path="/teacher/examinations" element={<ProtectedLayout><ClassExaminations /></ProtectedLayout>} />
      <Route path="/teacher/fees" element={<ProtectedLayout><FeeManagement /></ProtectedLayout>} />
      <Route path="/teacher/meetings" element={<ProtectedLayout><ClassMeetings /></ProtectedLayout>} />

      {/* Parent Portal Routes */}
      <Route path="/parent" element={<ProtectedLayout><ParentPortal /></ProtectedLayout>} />

      {/* Shared Operations Routes */}
      <Route path="/imports" element={<ProtectedLayout><ImportCenter /></ProtectedLayout>} />
      <Route path="/necta" element={<ProtectedLayout><NectaDashboard /></ProtectedLayout>} />
      <Route path="/ussd-simulator" element={<ProtectedLayout><UssdSimulator /></ProtectedLayout>} />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
