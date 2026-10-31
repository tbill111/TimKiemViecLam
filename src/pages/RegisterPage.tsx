import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { Briefcase, UserPlus } from 'lucide-react';
import { homePath, useAuth } from '../context/AuthContext';
import { errorMessage } from '../api/client';
import { OFFLINE } from '../config';

type SignUpRole = 'candidate' | 'recruiter';

export default function RegisterPage() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState<SignUpRole>('candidate');
  const [fullName, setFullName] = useState('');
  const [company, setCompany] = useState('');
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
      const u = await register({
        email: email.trim(),
        password,
        role,
        full_name: fullName.trim(),
        company_name: role === 'recruiter' ? company.trim() : undefined,
      });
      navigate(homePath(u.role), { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-8">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-2.5 mb-6">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
            <Briefcase size={20} className="text-white" />
          </div>
          <div className="font-bold text-slate-900 text-xl">SmartCareer</div>
        </div>

        <form onSubmit={submit} className="card p-6 space-y-4" aria-label="Đăng ký">
          <h1 className="text-lg font-bold text-slate-900">Tạo tài khoản</h1>
          {error && <div role="alert" className="p-2.5 bg-red-50 border border-red-100 rounded-lg text-sm text-red-700">{error}</div>}

          <fieldset>
            <legend className="block text-xs font-medium text-slate-500 mb-1.5">Bạn là</legend>
            <div className="grid grid-cols-2 gap-2">
              {([['candidate', 'Ứng viên / sinh viên'], ['recruiter', 'Nhà tuyển dụng']] as const).map(([value, label]) => (
                <label
                  key={value}
                  className={`flex items-center justify-center gap-2 p-2.5 rounded-lg border text-sm cursor-pointer ${
                    role === value ? 'border-blue-400 bg-blue-50 text-blue-700 font-medium' : 'border-slate-200 text-slate-600'
                  }`}
                >
                  <input type="radio" name="role" value={value} checked={role === value} onChange={() => setRole(value)} className="sr-only" />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>

          <div>
            <label htmlFor="reg-name" className="block text-xs font-medium text-slate-500 mb-1">Họ và tên</label>
            <input id="reg-name" required className="input-field" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          {role === 'recruiter' && (
            <div>
              <label htmlFor="reg-company" className="block text-xs font-medium text-slate-500 mb-1">Tên công ty</label>
              <input id="reg-company" required className="input-field" value={company} onChange={(e) => setCompany(e.target.value)} />
            </div>
          )}
          <div>
            <label htmlFor="reg-email" className="block text-xs font-medium text-slate-500 mb-1">Email</label>
            <input id="reg-email" type="email" required autoComplete="username" className="input-field" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label htmlFor="reg-password" className="block text-xs font-medium text-slate-500 mb-1">Mật khẩu (tối thiểu 8 ký tự)</label>
            <input id="reg-password" type="password" required minLength={8} maxLength={72} autoComplete="new-password" className="input-field" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <button type="submit" disabled={busy} className="btn-primary w-full justify-center">
            <UserPlus size={15} />
            {busy ? 'Đang tạo tài khoản...' : 'Đăng ký'}
          </button>
          <p className="text-sm text-slate-500 text-center">
            Đã có tài khoản? <Link to="/login" className="text-blue-600 font-medium hover:underline">Đăng nhập</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
