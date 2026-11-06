import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiErrorMessage, isOfflineDemo } from '../api/client';

export default function LoginPage() {
  const { login, loading, error } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');
  const submit = async (event: FormEvent) => { event.preventDefault(); setLocalError(''); try { const user = await login(email, password); navigate(user.role === 'candidate' ? '/' : user.role === 'admin' ? '/admin/skills' : '/employer/candidates'); } catch (requestError) { setLocalError(apiErrorMessage(requestError, 'Đăng nhập thất bại.')); } };
  const fill = (value: string) => { setEmail(value); setPassword('Demo@12345'); setLocalError(''); };
  return <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4"><div className="w-full max-w-md space-y-4"><form onSubmit={submit} className="card p-6 w-full space-y-4"><h1 className="text-xl font-bold">Đăng nhập SmartCareer</h1><input className="input-field" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required /><input className="input-field" type="password" placeholder="Mật khẩu" value={password} onChange={(e) => setPassword(e.target.value)} required />{isOfflineDemo && <p className="text-xs text-slate-500">Chế độ demo: nhập email bất kỳ. Bắt đầu bằng <code>hr</code> để xem màn nhà tuyển dụng, <code>admin</code> để xem màn quản trị.</p>}<p role="alert" className="text-sm text-red-600">{localError || error}</p><button className="btn-primary w-full justify-center" disabled={loading}>{loading ? 'Đang đăng nhập...' : 'Đăng nhập'}</button><p className="text-sm text-slate-500">Chưa có tài khoản? <Link className="text-blue-600" to="/register">Đăng ký</Link></p></form><div className="card p-4 text-xs text-slate-500 space-y-2"><div className="font-semibold text-slate-600">Tài khoản demo (mật khẩu Demo@12345)</div><div className="flex flex-wrap gap-2"><button type="button" className="btn-secondary text-xs py-1" onClick={() => fill('thanhtung.demo@smartcareer.vn')}>Ứng viên</button><button type="button" className="btn-secondary text-xs py-1" onClick={() => fill('hr1@smartcareer.vn')}>Nhà tuyển dụng</button><button type="button" className="btn-secondary text-xs py-1" onClick={() => fill('admin@smartcareer.vn')}>Quản trị</button></div></div></div></div>;
}
