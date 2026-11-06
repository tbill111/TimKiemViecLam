import { useEffect, useMemo, useRef, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { fetchBiData, fetchBiGuestToken, fetchBiSummary, type BiGuestToken, type BiRow, type BiSummary } from '../api/bi';
import { apiErrorMessage, isOfflineDemo } from '../api/client';
import { demoBi } from '../api/demoEmployer';
import LoadingBlock from '../components/ui/LoadingBlock';
import ErrorBlock from '../components/ui/ErrorBlock';
import EmptyBlock from '../components/ui/EmptyBlock';

const STAGE_LABEL: Record<string, string> = {
  applied: 'Đã ứng tuyển',
  screening: 'Đang xem xét',
  interview: 'Phỏng vấn',
  offer: 'Đề nghị',
  hired: 'Đã nhận việc',
  rejected: 'Từ chối',
};

const num = (value: string | number | null | undefined) => Number(value ?? 0);

/** Một nguồn dữ liệu có trạng thái riêng để lỗi của nguồn này không làm mất cả trang. */
interface Source<T> {
  data: T;
  error: string;
}

export default function EmployerDashboardPage() {
  const [summary, setSummary] = useState<Source<BiSummary | null>>({ data: null, error: '' });
  const [skills, setSkills] = useState<Source<BiRow[]>>({ data: [], error: '' });
  const [salary, setSalary] = useState<Source<BiRow[]>>({ data: [], error: '' });
  const [stages, setStages] = useState<Source<BiRow[]>>({ data: [], error: '' });
  const [guest, setGuest] = useState<BiGuestToken | null>(null);
  const [embedFailed, setEmbedFailed] = useState(false);
  const [loading, setLoading] = useState(true);
  const mountPoint = useRef<HTMLDivElement>(null);

  const load = async () => {
    if (isOfflineDemo) {
      const demo = demoBi();
      setSummary({ data: demo.summary, error: '' });
      setSkills({ data: demo.skills, error: '' });
      setSalary({ data: demo.salary, error: '' });
      setStages({ data: demo.stages, error: '' });
      setLoading(false);
      return;
    }
    setLoading(true);
    const settle = async <T,>(request: Promise<T>, message: string): Promise<Source<T | null>> => {
      try {
        return { data: await request, error: '' };
      } catch (reason) {
        return { data: null, error: apiErrorMessage(reason, message) };
      }
    };
    const [s, sk, sa, fu, token] = await Promise.all([
      settle(fetchBiSummary(), 'Không tải được số liệu tổng quan.'),
      settle(fetchBiData('skills'), 'Không tải được dữ liệu kỹ năng.'),
      settle(fetchBiData('salary'), 'Không tải được dữ liệu lương.'),
      settle(fetchBiData('funnel'), 'Không tải được phễu tuyển dụng.'),
      // Superset chưa cấu hình (503) là tình huống bình thường: dùng biểu đồ dự phòng bên dưới.
      fetchBiGuestToken().catch(() => null),
    ]);
    setSummary(s);
    setSkills({ data: sk.data?.items ?? [], error: sk.error });
    setSalary({ data: sa.data?.items ?? [], error: sa.error });
    setStages({ data: fu.data?.stages ?? [], error: fu.error });
    setGuest(token);
    setEmbedFailed(false);
    setLoading(false);
  };

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (!guest?.token || !guest.dashboard_id || !guest.superset_domain || !mountPoint.current) return;
    let active = true;
    const node = mountPoint.current;
    void import('@superset-ui/embedded-sdk')
      .then(({ embedDashboard }) => embedDashboard({
        id: guest.dashboard_id!,
        supersetDomain: guest.superset_domain!,
        mountPoint: node,
        fetchGuestToken: () => Promise.resolve(guest.token),
        dashboardUiConfig: { hideTitle: true, hideTab: true, hideChartControls: true, filters: { visible: false, expanded: false } },
      }))
      .catch(() => { if (active) setEmbedFailed(true); });
    return () => { active = false; node.replaceChildren(); };
  }, [guest]);

  const skillChart = useMemo(
    () => [...skills.data]
      .sort((a, b) => num(b.open_job_count) - num(a.open_job_count))
      .slice(0, 10)
      .map((row) => ({ name: String(row.skill_name), 'Số tin cần': num(row.open_job_count), 'Số ứng viên': num(row.candidate_count) })),
    [skills.data]
  );

  const salaryChart = useMemo(() => {
    const byMonth = new Map<string, { total: number; jobs: number }>();
    for (const row of salary.data) {
      const jobs = num(row.job_count);
      const mid = (num(row.average_salary_min) + num(row.average_salary_max)) / 2;
      const key = String(row.posted_month).slice(0, 7);
      const entry = byMonth.get(key) ?? { total: 0, jobs: 0 };
      byMonth.set(key, { total: entry.total + mid * jobs, jobs: entry.jobs + jobs });
    }
    return [...byMonth.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, v]) => ({ month, 'Lương trung bình': Math.round((v.total / Math.max(v.jobs, 1)) * 10) / 10 }));
  }, [salary.data]);

  const funnelChart = useMemo(() => {
    const byStage = new Map<string, { order: number; total: number }>();
    for (const row of stages.data) {
      const stage = String(row.stage);
      const entry = byStage.get(stage) ?? { order: num(row.stage_order), total: 0 };
      byStage.set(stage, { order: entry.order, total: entry.total + num(row.applications) });
    }
    return [...byStage.entries()]
      .sort(([, a], [, b]) => a.order - b.order)
      .map(([stage, v]) => ({ name: STAGE_LABEL[stage] ?? stage, 'Số hồ sơ': v.total }));
  }, [stages.data]);

  if (loading) return <LoadingBlock message="Đang tải dashboard BI..." />;
  const showEmbed = Boolean(guest?.dashboard_id) && !embedFailed;
  const cards: Array<[string, string | number]> = summary.data
    ? [['Ứng viên', summary.data.candidates], ['Tin đang mở', summary.data.open_jobs], ['Đơn ứng tuyển', summary.data.applications], ['Tỷ lệ nhận việc', `${summary.data.hire_rate}%`]]
    : [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Dashboard nhà tuyển dụng</h1>
        <p className="section-subtitle">Phễu tuyển dụng chỉ gồm các tin của công ty bạn; kỹ năng và lương là thị trường chung. Dữ liệu là mô phỏng.</p>
      </div>

      {showEmbed ? <div ref={mountPoint} className="card h-[1120px] overflow-hidden [&>iframe]:h-full [&>iframe]:w-full [&>iframe]:border-0" /> : isOfflineDemo ? (
        <p className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">Chế độ demo: số liệu dưới đây là dữ liệu mẫu, không lấy từ máy chủ.</p>
      ) : (
        <p className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">
          Dashboard Superset chưa sẵn sàng hoặc chưa được cấu hình, đang hiển thị biểu đồ dự phòng lấy từ API.
        </p>
      )}

      {summary.error ? <ErrorBlock message={summary.error} onRetry={() => void load()} /> : (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {cards.map(([label, value]) => (
            <div className="stat-card" key={label}><span className="text-sm text-slate-500">{label}</span><strong className="text-2xl">{value}</strong></div>
          ))}
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-2">
        <section className="card p-4">
          <h2 className="mb-3 font-semibold">Số ứng viên theo kỹ năng (cung) và số tin cần (cầu)</h2>
          {skills.error ? <ErrorBlock message={skills.error} onRetry={() => void load()} /> : skillChart.length === 0 ? <EmptyBlock message="Chưa có dữ liệu kỹ năng." /> : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={skillChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" interval={0} angle={-35} textAnchor="end" height={90} tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="Số ứng viên" fill="#2563eb" />
                <Bar dataKey="Số tin cần" fill="#f59e0b" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>

        <section className="card p-4">
          <h2 className="mb-3 font-semibold">Xu hướng lương theo tháng (triệu VNĐ/tháng)</h2>
          {salary.error ? <ErrorBlock message={salary.error} onRetry={() => void load()} /> : salaryChart.length === 0 ? <EmptyBlock message="Chưa có dữ liệu lương." /> : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={salaryChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="Lương trung bình" stroke="#059669" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </section>
      </div>

      <section className="card p-4">
        <h2 className="mb-3 font-semibold">Phễu tuyển dụng (số hồ sơ từng đạt mỗi bước)</h2>
        {stages.error ? <ErrorBlock message={stages.error} onRetry={() => void load()} /> : funnelChart.length === 0 ? <EmptyBlock message="Chưa có hồ sơ ứng tuyển." /> : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={funnelChart} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={110} />
              <Tooltip />
              <Bar dataKey="Số hồ sơ" fill="#7c3aed" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </section>
    </div>
  );
}
