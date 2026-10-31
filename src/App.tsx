import type { ReactNode } from 'react';
import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import { useAppState, type UseAppState } from './hooks/useAppState';
import { homePath, useAuth } from './context/AuthContext';
import { JobsProvider } from './context/JobsContext';
import { OFFLINE } from './config';
import type { Role } from './api/dto';
import LoadingBlock from './components/ui/LoadingBlock';
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
import EmployerPage from './pages/EmployerPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import EmployerJobsPage from './pages/EmployerJobsPage';
import PostJobPage from './pages/PostJobPage';
import EmployerCandidatesPage from './pages/EmployerCandidatesPage';
import EmployerDashboardPage from './pages/EmployerDashboardPage';

export default function App() {
  const appState = useAppState();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        {/* Xem sơ đồ toàn màn hình, không có sidebar */}
        <Route path="/dfd/view/:level" element={<DfdFullView />} />
        <Route path="*" element={<AppShell appState={appState} />} />
      </Routes>
    </BrowserRouter>
  );
}

/** Chặn route theo vai trò. Chế độ demo (không backend) cho vào mọi trang. */
function RoleRoute({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { user } = useAuth();
  if (OFFLINE) return <>{children}</>;
  if (!user || !roles.includes(user.role)) return <Navigate to={homePath(user?.role)} replace />;
  return <>{children}</>;
}

const CANDIDATE: Role[] = ['candidate'];
const STAFF: Role[] = ['recruiter', 'admin'];

/** Các trang có sidebar. */
function AppShell({ appState }: { appState: UseAppState }) {
  const { user, ready } = useAuth();

  if (!OFFLINE) {
    if (!ready) return <div className="p-8 max-w-xl mx-auto"><LoadingBlock rows={1} message="Đang kiểm tra phiên đăng nhập..." /></div>;
    if (!user) return <Navigate to="/login" replace />;
  }

  const candidate = (el: ReactNode) => <RoleRoute roles={CANDIDATE}>{el}</RoleRoute>;
  const staff = (el: ReactNode) => (OFFLINE ? <Navigate to="/employer" replace /> : <RoleRoute roles={STAFF}>{el}</RoleRoute>);

  return (
    <JobsProvider profile={appState.studentProfile}>
      <MainLayout appState={appState}>
        <Routes>
          <Route path="/" element={candidate(<DashboardPage appState={appState} />)} />
          <Route path="/jobs" element={candidate(<JobsPage appState={appState} />)} />
          <Route path="/match" element={candidate(<MatchPage appState={appState} />)} />
          <Route path="/skill-gap" element={candidate(<SkillGapPage appState={appState} />)} />
          <Route path="/applications" element={candidate(<ApplicationsPage appState={appState} />)} />
          <Route path="/profile" element={candidate(<ProfilePage appState={appState} />)} />

          {/* Cổng nhà tuyển dụng: demo dùng bản mô phỏng; online dùng 4 trang gọi API */}
          <Route path="/employer" element={OFFLINE ? <EmployerPage appState={appState} /> : <Navigate to="/employer/candidates" replace />} />
          <Route path="/employer/dashboard" element={staff(<EmployerDashboardPage />)} />
          <Route path="/employer/jobs" element={staff(<EmployerJobsPage />)} />
          <Route path="/employer/jobs/new" element={staff(<PostJobPage />)} />
          <Route path="/employer/jobs/:id/edit" element={staff(<PostJobPage />)} />
          <Route path="/employer/candidates" element={staff(<EmployerCandidatesPage />)} />

          <Route path="/etl" element={<ETLPage appState={appState} />} />
          <Route path="/dfd" element={<DFDPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route
            path="*"
            element={
              <div className="text-center py-20">
                <h2 className="text-xl font-bold text-slate-700 mb-2">Trang không tồn tại</h2>
                <a href="/" className="text-blue-600 hover:underline text-sm">← Về trang chủ</a>
              </div>
            }
          />
        </Routes>
      </MainLayout>
    </JobsProvider>
  );
}
