import { useEffect, useRef, useState } from 'react';
import { BarChart, Bar, CartesianGrid, LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { fetchBiData, fetchBiGuestToken, fetchBiSummary, type BiRow, type BiSummary } from '../api/bi';
import { isOfflineDemo, apiErrorMessage } from '../api/client';
import LoadingBlock from '../components/ui/LoadingBlock';
import ErrorBlock from '../components/ui/ErrorBlock';
export default function EmployerDashboardPage() {
  const [summary, setSummary] = useState<BiSummary | null>(null); const [skills, setSkills] = useState<BiRow[]>([]); const [salary, setSalary] = useState<BiRow[]>([]); const [guest, setGuest] = useState<{ token: string; dashboard_id?: string; superset_domain?: string } | null>(null); const [error, setError] = useState(''); const [loading, setLoading] = useState(!isOfflineDemo); const mountPoint = useRef<HTMLDivElement>(null);
  useEffect(() => { if (isOfflineDemo) return; void Promise.all([fetchBiSummary(), fetchBiData('skills'), fetchBiData('salary'), fetchBiGuestToken()]).then(([s, sk, sa, token]) => { setSummary(s); setSkills(sk.items); setSalary(sa.items); setGuest(token); }).catch((e: unknown) => setError(apiErrorMessage(e, 'Không tải được BI.'))).finally(() => setLoading(false)); }, []);
  useEffect(() => {
    if (!guest?.token || !guest.dashboard_id || !guest.superset_domain || !mountPoint.current) return;
    let active = true;
    void import('@superset-ui/embedded-sdk').then(({ embedDashboard }) => embedDashboard({
      id: guest.dashboard_id!,
      supersetDomain: guest.superset_domain!,
      mountPoint: mountPoint.current!,
      fetchGuestToken: () => Promise.resolve(guest.token),
      dashboardUiConfig: { hideTitle: true, hideTab: true, hideChartControls: true },
    })).then(() => { if (active) setGuest((current) => current); }).catch(() => { if (active) setGuest(null); });
    return () => { active = false; if (mountPoint.current) mountPoint.current.replaceChildren(); };
  }, [guest]);
  if (loading) return <LoadingBlock message="Đang tải dashboard BI..." />;
  if (error) return <ErrorBlock message={error} />;
  return <div className="space-y-5"><h1 className="text-2xl font-bold">Dashboard nhà tuyển dụng</h1>{guest?.dashboard_id && <div ref={mountPoint} className="card min-h-64" />} {summary && <div className="grid grid-cols-2 md:grid-cols-4 gap-3">{[['Ứng viên', summary.candidates], ['Tin đang mở', summary.open_jobs], ['Đơn ứng tuyển', summary.applications], ['Tỷ lệ nhận việc', `${summary.hire_rate}%`]].map(([label, value]) => <div className="stat-card" key={String(label)}><span className="text-sm text-slate-500">{label}</span><strong className="text-2xl">{value}</strong></div>)}</div>}<div className="grid lg:grid-cols-2 gap-5"><div className="card p-4"><h2 className="font-semibold mb-3">Kỹ năng cung/cầu</h2><ResponsiveContainer width="100%" height={280}><BarChart data={skills.slice(0, 10)}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="skill" hide /><YAxis /><Tooltip /><Bar dataKey="demand" fill="#2563eb" /></BarChart></ResponsiveContainer></div><div className="card p-4"><h2 className="font-semibold mb-3">Xu hướng lương</h2><ResponsiveContainer width="100%" height={280}><LineChart data={salary}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="month" /><YAxis /><Tooltip /><Line type="monotone" dataKey="median_salary" stroke="#059669" /></LineChart></ResponsiveContainer></div></div></div>;
}
