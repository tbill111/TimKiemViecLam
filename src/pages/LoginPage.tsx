import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { Briefcase, LogIn } from 'lucide-react';
import { homePath, useAuth } from '../context/AuthContext';
import { errorMessage } from '../api/client';
import { OFFLINE } from '../config';

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (OFFLINE) return <Navigate to="/" replace />;
  if (user) return <Navigate to={homePath(user.role)} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const u = await login(email.trim(), password);
      navigate(homePath(u.role), { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const fill = (e: string) => {
    setEmail(e);
    setPassword('Demo@12345');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-2.5 mb-6">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
            <Briefcase size={20} className="text-white" />
          </div>
          <div>
            <div className="font-bold text-slate-900 text-xl leading-tight">SmartCareer</div>
            <div className="text-xs text-slate-400">Hệ thống Tìm việc Thông minh tích hợp AI và BI</div>
          </div>
        </div>

        <form onSubmit={submit} className="card p-6 space-y-4" aria-label="Đăng nhập">
          <h1 className="text-lg font-bold text-slate-900">Đăng nhập</h1>
          {error && <div role="alert" className="p-2.5 bg-red-50 border border-red-100 rounded-lg text-sm text-red-700">{error}</div>}
          <div>
            <label htmlFor="login-email" className="block text-xs font-medium text-slate-500 mb-1">Email</label>
            <input id="login-email" type="email" required autoComplete="username" className="input-field" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label htmlFor="login-password" className="block text-xs font-medium text-slate-500 mb-1">Mật khẩu</label>
            <input id="login-password" type="password" required autoComplete="current-password" className="input-field" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <button type="submit" disabled={busy} className="btn-primary w-full justify-center">
            <LogIn size={15} />
            {busy ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
          <p className="text-sm text-slate-500 text-center">
            Chưa có tài khoản? <Link to="/register" className="text-blue-600 font-medium hover:underline">Đăng ký</Link>
          </p>
        </form>

        <div className="mt-4 card p-4 text-xs text-slate-500 space-y-2">
          <div className="font-semibold text-slate-600">Tài khoản demo (mật khẩu Demo@12345)</div>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn-secondary text-xs py-1" onClick={() => fill('tung.demo@smartcareer.vn')}>Ứng viên</button>
            <button type="button" className="btn-secondary text-xs py-1" onClick={() => fill('hr01@smartcareer.vn')}>Nhà tuyển dụng</button>
            <button type="button" className="btn-secondary text-xs py-1" onClick={() => fill('admin@smartcareer.vn')}>Quản trị</button>
          </div>
        </div>
      </div>
    </div>
  );
}
