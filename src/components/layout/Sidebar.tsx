import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  Briefcase,
  UserCircle,
  BarChart2,
  TrendingUp,
  Database,
  GitFork,
  Info,
  Bookmark,
  RotateCcw,
  Building2,
} from 'lucide-react';
import { useMemo } from 'react';
import type { UseAppState } from '../../hooks/useAppState';
import { countSuitableJobs } from '../../utils';

interface SidebarProps {
  appState: UseAppState;
  /** Trạng thái mở trên màn hình nhỏ (dưới md). Trên màn hình lớn sidebar luôn hiển thị. */
  open: boolean;
  onClose: () => void;
}

const navItems = [
  { to: '/', label: 'Tổng quan', icon: LayoutDashboard, end: true },
  { to: '/jobs', label: 'Tìm việc làm', icon: Search },
  { to: '/match', label: 'Phân tích CV–JD', icon: BarChart2 },
  { to: '/skill-gap', label: 'Skill Gap Analysis', icon: TrendingUp },
  { to: '/applications', label: 'Việc đã lưu & Ứng tuyển', icon: Bookmark },
  { to: '/profile', label: 'Hồ sơ của tôi', icon: UserCircle },
  { to: '/employer', label: 'Cổng nhà tuyển dụng', icon: Building2 },
];

const systemItems = [
  { to: '/etl', label: 'Trung tâm Dữ liệu & ETL', icon: Database },
  { to: '/dfd', label: 'Sơ đồ Luồng Dữ liệu', icon: GitFork },
  { to: '/about', label: 'Về SmartCareer', icon: Info },
];

export default function Sidebar({ appState, open, onClose }: SidebarProps) {
  const navigate = useNavigate();
  const { studentProfile, savedJobs, applications, resetToDemo } = appState;

  const suitableCount = useMemo(() => countSuitableJobs(studentProfile), [studentProfile]);

  const handleReset = () => {
    if (window.confirm('Đặt lại toàn bộ dữ liệu về trạng thái demo ban đầu?')) {
      resetToDemo();
      onClose();
      navigate('/');
    }
  };

  const panelState = open ? 'translate-x-0' : '-translate-x-full';

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-slate-200 flex flex-col transform transition-transform duration-200 md:static md:min-h-screen md:translate-x-0 md:shrink-0 ${panelState}`}
    >
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Briefcase size={16} className="text-white" />
          </div>
          <div>
            <div className="font-bold text-slate-900 text-base leading-tight">SmartCareer</div>
            <div className="text-xs text-slate-400 leading-tight">Hệ thống Tìm việc Thông minh</div>
          </div>
        </div>
      </div>

      {/* Student mini-profile */}
      <div className="px-4 py-3 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-sm shrink-0">
            {studentProfile.fullName.split(' ').slice(-2).map((n) => n[0]).join('')}
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold text-slate-800 truncate">{studentProfile.fullName}</div>
            <div className="text-xs text-slate-400 truncate">{studentProfile.major}</div>
          </div>
        </div>
        <div className="mt-2.5">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-slate-400">Hoàn thiện hồ sơ</span>
            <span className="text-xs font-semibold text-blue-600">{studentProfile.profileCompletion}%</span>
          </div>
          <div className="progress-bar h-1.5">
            <div
              className="progress-fill bg-blue-500"
              style={{ width: `${studentProfile.profileCompletion}%` }}
            />
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-3 overflow-y-auto scrollbar-thin">
        <div className="space-y-0.5">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onClose}
              className={({ isActive }) => (isActive ? 'nav-active block' : 'nav-inactive block')}
            >
              <item.icon size={16} className="shrink-0" />
              <span className="flex-1">{item.label}</span>
            </NavLink>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t border-slate-100">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">
            Hệ thống & Kiến trúc
          </div>
          <div className="space-y-0.5">
            {systemItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) => (isActive ? 'nav-active block' : 'nav-inactive block')}
              >
                <item.icon size={16} className="shrink-0" />
                <span className="flex-1">{item.label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </nav>

      {/* Quick stats */}
      <div className="px-4 py-3 border-t border-slate-100 bg-slate-50">
        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="text-center">
            <div className="text-base font-bold text-blue-600">{applications.length}</div>
            <div className="text-xs text-slate-400 leading-tight">Ứng tuyển</div>
          </div>
          <div className="text-center">
            <div className="text-base font-bold text-emerald-600">{savedJobs.length}</div>
            <div className="text-xs text-slate-400 leading-tight">Đã lưu</div>
          </div>
          <div className="text-center">
            <div className="text-base font-bold text-slate-600">{suitableCount}</div>
            <div className="text-xs text-slate-400 leading-tight">Việc phù hợp</div>
          </div>
        </div>
        <button
          onClick={handleReset}
          className="w-full flex items-center justify-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 transition-colors py-1"
        >
          <RotateCcw size={12} />
          Đặt lại dữ liệu demo
        </button>
      </div>
    </aside>
  );
}
