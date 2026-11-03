import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiErrorMessage } from '../api/client';

export default function RegisterPage() {
  const { register, loading } = useAuth(); const navigate = useNavigate();
  const [form, setForm] = useState({ fullName: '', email: '', password: '', role: 'candidate' as 'candidate' | 'recruiter', companyName: '' }); const [error, setError] = useState('');
  const submit = async (event: FormEvent) => { event.preventDefault(); try { const user = await register(form); navigate(user.role === 'candidate' ? '/' : '/employer/candidates'); } catch (requestError) { setError(apiErrorMessage(requestError, 'Đăng ký thất bại.')); } };
  return <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4"><form onSubmit={submit} className="card p-6 w-full max-w-md space-y-4"><h1 className="text-xl font-bold">Tạo tài khoản</h1><input className="input-field" placeholder="Họ và tên" value={form.fullName} onChange={(e) => setForm({ ...form, fullName: e.target.value })} required /><input className="input-field" type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /><input className="input-field" type="password" minLength={8} placeholder="Mật khẩu" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /><select className="select-field" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as 'candidate' | 'recruiter' })}><option value="candidate">Ứng viên</option><option value="recruiter">Nhà tuyển dụng</option></select>{form.role === 'recruiter' && <input className="input-field" placeholder="Tên công ty" value={form.companyName} onChange={(e) => setForm({ ...form, companyName: e.target.value })} required />}<p role="alert" className="text-sm text-red-600">{error}</p><button className="btn-primary w-full justify-center" disabled={loading}>Đăng ký</button><p className="text-sm text-slate-500">Đã có tài khoản? <Link className="text-blue-600" to="/login">Đăng nhập</Link></p></form></div>;
}
