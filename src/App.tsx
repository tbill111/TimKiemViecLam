import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom';
import type { ReactNode } from 'react';
import MainLayout from './components/layout/MainLayout';
import { useAppState, type UseAppState } from './hooks/useAppState';
import DfdFullView from './pages/DfdFullView';
import DashboardPage from './pages/DashboardPage';
import JobsPage from './pages/JobsPage';
import MatchPage from './pages/MatchPage';
import SkillGapPage from './pages/SkillGapPage';
import ApplicationsPage from './pages/ApplicationsPage';
import ProfilePage from './pages/ProfilePage';
import ETLPage from './pages/ETLPage';
import DFDPage from './pages/DFDPage';
import AboutPage from './pages/AboutPage';
import { AuthProvider } from './context/AuthContext';
import { JobsProvider } from './context/JobsContext';
import { useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import EmployerJobsPage from './pages/EmployerJobsPage';
import PostJobPage from './pages/PostJobPage';
import EditJobPage from './pages/EditJobPage';
import EmployerCandidatesPage from './pages/EmployerCandidatesPage';
import EmployerKanbanPage from './pages/EmployerKanbanPage';
import EmployerDashboardPage from './pages/EmployerDashboardPage';
import AdminSkillsPage from './pages/AdminSkillsPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

function AppContent() {
  const appState = useAppState();
  return (
    <JobsProvider>
      <Routes>
        <Route path="/login" element={<GuestRoute><LoginPage /></GuestRoute>} />
        <Route path="/register" element={<GuestRoute><RegisterPage /></GuestRoute>} />
        <Route path="/dfd/view/:level" element={<DfdFullView />} />
        <Route path="*" element={<AppShell appState={appState} />} />
      </Routes>
    </JobsProvider>
  );
}

/** Các trang có sidebar. */
function AppShell({ appState }: { appState: UseAppState }) {
  return (
    <MainLayout appState={appState}>
      <Routes>
        <Route path="/" element={<ProtectedRoute roles={['candidate']}><DashboardPage appState={appState} /></ProtectedRoute>} />
        <Route path="/jobs" element={<ProtectedRoute roles={['candidate']}><JobsPage appState={appState} /></ProtectedRoute>} />
        <Route path="/match" element={<ProtectedRoute roles={['candidate']}><MatchPage appState={appState} /></ProtectedRoute>} />
        <Route path="/skill-gap" element={<ProtectedRoute roles={['candidate']}><SkillGapPage appState={appState} /></ProtectedRoute>} />
        <Route path="/applications" element={<ProtectedRoute roles={['candidate']}><ApplicationsPage appState={appState} /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute roles={['candidate']}><ProfilePage appState={appState} /></ProtectedRoute>} />
        <Route path="/employer" element={<Navigate to="/employer/candidates" replace />} />
        <Route path="/employer/dashboard" element={<ProtectedRoute roles={['recruiter']}><EmployerDashboardPage /></ProtectedRoute>} />
        <Route path="/employer/jobs" element={<ProtectedRoute roles={['recruiter']}><EmployerJobsPage /></ProtectedRoute>} />
        <Route path="/employer/jobs/new" element={<ProtectedRoute roles={['recruiter']}><PostJobPage /></ProtectedRoute>} />
        <Route path="/employer/jobs/:id/edit" element={<ProtectedRoute roles={['recruiter']}><EditJobPage /></ProtectedRoute>} />
        <Route path="/employer/candidates" element={<ProtectedRoute roles={['recruiter']}><EmployerCandidatesPage /></ProtectedRoute>} />
        <Route path="/employer/kanban" element={<ProtectedRoute roles={['recruiter']}><EmployerKanbanPage /></ProtectedRoute>} />
        <Route path="/admin/skills" element={<ProtectedRoute roles={['admin']}><AdminSkillsPage /></ProtectedRoute>} />
        <Route path="/etl" element={<ETLPage appState={appState} />} />
        <Route path="/dfd" element={<DFDPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="*" element={
          <div className="text-center py-20">
            <h2 className="text-xl font-bold text-slate-700 mb-2">Trang không tồn tại</h2>
            <a href="/" className="text-blue-600 hover:underline text-sm">← Về trang chủ</a>
          </div>
        } />
      </Routes>
    </MainLayout>
  );
}

function ProtectedRoute({ roles, children }: { roles: Array<'candidate' | 'recruiter' | 'admin'>; children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-10 text-center text-slate-500">Đang kiểm tra phiên đăng nhập...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <div className="card p-10 text-center">Bạn không có quyền truy cập trang này.</div>;
  return <>{children}</>;
}

function GuestRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-10 text-center text-slate-500">Đang kiểm tra phiên đăng nhập...</div>;
  if (user) return <Navigate to={user.role === 'candidate' ? '/' : user.role === 'admin' ? '/admin/skills' : '/employer/candidates'} replace />;
  return <>{children}</>;
}
