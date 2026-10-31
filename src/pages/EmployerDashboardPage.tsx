import { useEffect, useMemo, useRef, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Info } from 'lucide-react';
import { biApi } from '../api/endpoints';
import { errorCode, errorMessage } from '../api/client';
import type { BiFunnel, BiSalary, BiSkillRow, BiSummary } from '../api/dto';
import { STATUS_LABEL } from '../api/adapters';
import type { ApiStatus } from '../api/dto';
import LoadingBlock from '../components/ui/LoadingBlock';
import ErrorBlock from '../components/ui/ErrorBlock';

const LEVEL_COLORS: Record<string, string> = { intern: '#94a3b8', fresher: '#3b82f6', junior: '#10b981', middle: '#f59e0b', senior: '#ef4444' };
const LEVELS = ['intern', 'fresher', 'junior', 'middle', 'senior'];

type EmbedState = 'trying' | 'embedded' | 'fallback';

/** Dashboard BI: nhúng Superset khi có; nếu lỗi/chưa cấu hình thì vẽ 3 biểu đồ bắt buộc bằng Recharts từ /api/bi/*. */
export default function EmployerDashboardPage() {
  const [summary, setSummary] = useState<BiSummary | null>(null);
  const [skills, setSkills] = useState<BiSkillRow[] | null>(null);
  const [salary, setSalary] = useState<BiSalary | null>(null);
  const [funnel, setFunnel] = useState<BiFunnel | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [embed, setEmbed] = useState<EmbedState>('trying');
  const [embedReason, setEmbedReason] = useState<string>('');
  const mount = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([biApi.summary(), biApi.skills(), biApi.salary(), biApi.funnel()])
      .then(([a, b, c, d]) => {
        setSummary(a);
        setSkills(b);
        setSalary(c);
        setFunnel(d);
      })
      .catch((e) => setError(errorMessage(e)));
  }, []);

  // Thử nhúng Superset bằng guest token (RLS theo công ty được áp ở backend)
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const g = await biApi.guestToken();
        const { embedDashboard } = await import('@superset-ui/embedded-sdk');
        if (cancelled || !mount.current) return;
        await embedDashboard({
          id: g.dashboard_id,
          supersetDomain: g.superset_domain,
          mountPoint: mount.current,
          fetchGuestToken: () => Promise.resolve(g.token),
          dashboardUiConfig: { hideTitle: true, hideChartControls: true },
        });
        const iframe = mount.current.querySelector('iframe');
        if (iframe) {
          iframe.style.width = '100%';
          iframe.style.height = '720px';
          iframe.style.border = '0';
        }
        if (!cancelled) setEmbed('embedded');
      } catch (e) {
        if (cancelled) return;
        setEmbedReason(errorCode(e) === 'superset_not_configured' ? 'Superset chưa được cấu hình' : errorMessage(e));
        setEmbed('fallback');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const topSkills = useMemo(() => (skills ?? []).slice(0, 15), [skills]);

  const salaryByMonth = useMemo(() => {
    const months = new Map<string, Record<string, number | string>>();
    for (const r of salary?.items ?? []) {
      const row = months.get(r.month) ?? { month: r.month };
      row[r.level] = r.median_salary;
      months.set(r.month, row);
    }
    return [...months.values()].sort((a, b) => String(a.month).localeCompare(String(b.month)));
  }, [salary]);

  const funnelData = useMemo(
    () => (funnel?.stages ?? []).map((s) => ({ ...s, label: STATUS_LABEL[s.stage as ApiStatus] ?? s.stage })),
    [funnel]
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard thị trường tuyển dụng</h1>
        <p className="text-slate-500 text-sm mt-0.5">Số ứng viên theo kỹ năng, xu hướng lương và tỷ lệ chuyển đổi tuyển dụng.</p>
      </div>

      {error && <ErrorBlock message={error} />}

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            ['Ứng viên', summary.candidates.toLocaleString('vi-VN')],
            ['Tin đang mở', summary.open_jobs.toLocaleString('vi-VN')],
            ['Hồ sơ đã nộp', summary.applications.toLocaleString('vi-VN')],
            ['Tỷ lệ tuyển', `${(summary.hire_rate * 100).toFixed(1)}%`],
          ].map(([label, value]) => (
            <div key={label} className="stat-card">
              <div className="text-xs text-slate-400 uppercase tracking-wide">{label}</div>
              <div className="text-3xl font-bold text-slate-900">{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Superset nhúng */}
      <div ref={mount} className={embed === 'embedded' ? 'card overflow-hidden' : 'hidden'} data-testid="superset-mount" />
      {embed === 'trying' && <LoadingBlock rows={1} message="Đang kết nối Superset..." />}

      {embed === 'fallback' && (
        <>
          <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-100 rounded-xl text-sm text-amber-700">
            <Info size={16} className="shrink-0 mt-0.5" />
            <span>
              Không nhúng được dashboard Superset ({embedReason}). Hiển thị 3 biểu đồ bắt buộc từ cùng số liệu của các view BI.
              Dữ liệu ứng tuyển và lương là mô phỏng.
            </span>
          </div>

          {!skills || !salary || !funnel ? (
            !error && <LoadingBlock rows={2} message="Đang tải số liệu..." />
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <section className="card p-5 xl:col-span-2" aria-label="Số ứng viên theo kỹ năng">
                <h2 className="font-semibold text-sm text-slate-800 mb-1">Top 15 kỹ năng theo số ứng viên và nhu cầu tuyển</h2>
                <p className="text-xs text-slate-400 mb-3">Ứng viên đã xác nhận kỹ năng so với số tin đang mở yêu cầu kỹ năng đó.</p>
                <div style={{ width: '100%', height: 340 }}>
                  <ResponsiveContainer>
                    <BarChart data={topSkills} margin={{ top: 5, right: 10, left: 0, bottom: 60 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="skill" angle={-35} textAnchor="end" interval={0} height={70} tick={{ fontSize: 11 }} />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Legend verticalAlign="top" />
                      <Bar dataKey="so_ung_vien" name="Số ứng viên" fill="#3b82f6" isAnimationActive={false} />
                      <Bar dataKey="so_tin_yeu_cau" name="Số tin yêu cầu" fill="#f59e0b" isAnimationActive={false} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </section>

              <section className="card p-5" aria-label="Xu hướng lương">
                <h2 className="font-semibold text-sm text-slate-800 mb-1">Trung vị lương theo tháng đăng và cấp bậc</h2>
                <p className="text-xs text-slate-400 mb-3">Triệu VNĐ/tháng, không tính tin thỏa thuận.</p>
                <div style={{ width: '100%', height: 320 }}>
                  <ResponsiveContainer>
                    <LineChart data={salaryByMonth} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      {LEVELS.map((lv) => (
                        <Line key={lv} type="monotone" dataKey={lv} name={lv} stroke={LEVEL_COLORS[lv]} dot={{ r: 2 }} connectNulls isAnimationActive={false} />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </section>

              <section className="card p-5" aria-label="Tỷ lệ chuyển đổi tuyển dụng">
                <h2 className="font-semibold text-sm text-slate-800 mb-1">Phễu tuyển dụng (hồ sơ từng đạt mỗi bước)</h2>
                <p className="text-xs text-slate-400 mb-3">
                  Chuyển đổi tổng: {funnel.total_conversion == null ? '—' : `${(funnel.total_conversion * 100).toFixed(1)}%`}
                  {funnel.median_time_to_hire_days != null && ` · trung vị ${funnel.median_time_to_hire_days} ngày đến khi tuyển`}
                </p>
                <div style={{ width: '100%', height: 250 }}>
                  <ResponsiveContainer>
                    <BarChart data={funnelData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" allowDecimals={false} />
                      <YAxis type="category" dataKey="label" width={95} tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="count" name="Số hồ sơ" fill="#10b981" isAnimationActive={false} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <table className="w-full text-xs mt-3">
                  <thead>
                    <tr className="text-left text-slate-400"><th className="py-1">Bước</th><th>Số hồ sơ</th><th>So với bước trước</th></tr>
                  </thead>
                  <tbody>
                    {funnelData.map((s) => (
                      <tr key={s.stage} className="border-t border-slate-100">
                        <td className="py-1">{s.label}</td>
                        <td>{s.count}</td>
                        <td>{s.conversion_from_prev == null ? '—' : `${(s.conversion_from_prev * 100).toFixed(1)}%`}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>
            </div>
          )}
        </>
      )}
    </div>
  );
}
