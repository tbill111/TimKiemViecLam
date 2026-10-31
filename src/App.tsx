import { BrowserRouter, Routes, Route } from 'react-router-dom';
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
import EmployerPage from './pages/EmployerPage';

export default function App() {
  const appState = useAppState();

  return (
    <BrowserRouter>
      <Routes>
        {/* Xem sơ đồ toàn màn hình, không có sidebar */}
        <Route path="/dfd/view/:level" element={<DfdFullView />} />
        <Route path="*" element={<AppShell appState={appState} />} />
      </Routes>
    </BrowserRouter>
  );
}

/** Các trang có sidebar. */
function AppShell({ appState }: { appState: UseAppState }) {
  return (
    <MainLayout appState={appState}>
      <Routes>
        <Route path="/" element={<DashboardPage appState={appState} />} />
        <Route path="/jobs" element={<JobsPage appState={appState} />} />
        <Route path="/match" element={<MatchPage appState={appState} />} />
        <Route path="/skill-gap" element={<SkillGapPage appState={appState} />} />
        <Route path="/applications" element={<ApplicationsPage appState={appState} />} />
        <Route path="/profile" element={<ProfilePage appState={appState} />} />
        <Route path="/employer" element={<EmployerPage appState={appState} />} />
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
