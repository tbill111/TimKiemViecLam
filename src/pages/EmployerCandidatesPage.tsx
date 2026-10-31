import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { CheckCircle2, ChevronRight, Star, XCircle } from 'lucide-react';
import { aiApi, applicationApi, jobsApi } from '../api/endpoints';
import { STATUS_LABEL, allowedNext, toJob } from '../api/adapters';
import { errorMessage } from '../api/client';
import type { ApiStatus, ModelId, RankedCandidateDTO } from '../api/dto';
import type { Job } from '../types';
import { getMatchColorClass } from '../utils';
import LoadingBlock from '../components/ui/LoadingBlock';
import ErrorBlock from '../components/ui/ErrorBlock';
import EmptyBlock from '../components/ui/EmptyBlock';

const COLUMNS: ApiStatus[] = ['applied', 'screening', 'interview', 'offer', 'hired', 'rejected'];
const COLUMN_STYLE: Record<ApiStatus, string> = {
  applied: 'border-blue-200 bg-blue-50/50',
  screening: 'border-amber-200 bg-amber-50/50',
  interview: 'border-purple-200 bg-purple-50/50',
  offer: 'border-teal-200 bg-teal-50/50',
  hired: 'border-emerald-200 bg-emerald-50/50',
  rejected: 'border-slate-200 bg-slate-50',
};
const MODELS: ModelId[] = ['m0', 'm1', 'm2', 'm3', 'm4'];

/** Bảng Kanban 6 cột: ứng viên đã nộp vào tin của công ty, xếp theo điểm khớp; chuyển trạng thái theo đúng luồng phễu. */
export default function EmployerCandidatesPage() {
  const [params, setParams] = useSearchParams();
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [items, setItems] = useState<RankedCandidateDTO[] | null>(null);
  const [model, setModel] = useState<ModelId>('m3');
  const [error, setError] = useState<string | null>(null);
  const [busyApp, setBusyApp] = useState<number | null>(null);

  const jobId = params.get('job') ?? jobs?.[0]?.id ?? '';

  useEffect(() => {
    jobsApi
      .list({ mine: true, sort: 'newest' })
      .then((r) => setJobs(r.items.map(toJob)))
      .catch((e) => setError(errorMessage(e)));
  }, []);

  const load = useCallback(() => {
    if (!jobId) return;
    setError(null);
    aiApi
      .ranked(jobId, 200, model)
      .then(setItems)
      .catch((e) => {
        setItems(null);
        setError(errorMessage(e));
      });
  }, [jobId, model]);

  useEffect(() => {
    setItems(null);
    load();
  }, [load]);

  const change = async (applicationId: number, status: ApiStatus) => {
    setBusyApp(applicationId);
    setError(null);
    try {
      await applicationApi.setStatus(applicationId, status);
      load();
    } catch (e) {
      setError(errorMessage(e)); // ví dụ 409 khi nhảy cóc trạng thái
    } finally {
      setBusyApp(null);
    }
  };

  const byStatus = useMemo(() => {
    const map = new Map<ApiStatus, RankedCandidateDTO[]>(COLUMNS.map((c) => [c, []]));
    for (const it of items ?? []) map.get(it.status)?.push(it);
    return map;
  }, [items]);

  const job = jobs?.find((j) => j.id === jobId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Ứng viên xếp hạng</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Chỉ hiển thị ứng viên đã nộp hồ sơ vào tin của công ty bạn. Điểm là gợi ý hỗ trợ quyết định; mô hình không dùng tên, giới tính hay tuổi.
        </p>
      </div>

      <div className="card p-5 flex flex-col md:flex-row md:items-end gap-4">
        <div className="flex-1 min-w-0">
          <label htmlFor="rk-job" className="block text-xs font-medium text-slate-500 mb-1.5">Tin tuyển dụng</label>
          <select id="rk-job" className="select-field" value={jobId} onChange={(e) => setParams({ job: e.target.value })} disabled={!jobs?.length}>
            {(jobs ?? []).map((j) => (
              <option key={j.id} value={j.id}>{j.title} ({j.status === 'open' ? 'đang mở' : 'đã đóng'})</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="rk-model" className="block text-xs font-medium text-slate-500 mb-1.5">Mô hình xếp hạng</label>
          <select id="rk-model" className="select-field" value={model} onChange={(e) => setModel(e.target.value as ModelId)}>
            {MODELS.map((m) => <option key={m} value={m}>{m.toUpperCase()}</option>)}
          </select>
        </div>
      </div>

      {job && <p className="text-xs text-slate-500">Yêu cầu bắt buộc: {job.requiredSkills.join(', ')}</p>}
      {error && <ErrorBlock message={error} onRetry={load} />}
      {jobs && jobs.length === 0 && <EmptyBlock title="Công ty chưa có tin tuyển dụng" hint="Đăng tin để nhận hồ sơ ứng viên." />}
      {jobId && !items && !error && <LoadingBlock rows={2} message="Đang chấm điểm và xếp hạng ứng viên..." />}
      {items && items.length === 0 && <EmptyBlock title="Chưa có ứng viên nộp hồ sơ" hint="Hồ sơ sẽ xuất hiện ở đây khi ứng viên ứng tuyển." />}

      {items && items.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4" role="list" aria-label="Bảng Kanban trạng thái hồ sơ">
          {COLUMNS.map((status) => {
            const col = byStatus.get(status) ?? [];
            return (
              <section key={status} role="listitem" className={`rounded-xl border p-3 ${COLUMN_STYLE[status]}`} aria-label={STATUS_LABEL[status]}>
                <h2 className="flex items-center justify-between text-sm font-semibold text-slate-700 mb-3">
                  {STATUS_LABEL[status]}
                  <span className="badge-gray">{col.length}</span>
                </h2>
                <div className="space-y-2">
                  {col.map((it) => {
                    const m = it.match;
                    const next = allowedNext(it.status);
                    return (
                      <article key={it.application_id} className="card p-3 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div className="font-semibold text-sm text-slate-800">{it.full_name}</div>
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold ${getMatchColorClass(m.total_score)}`}>
                            <Star size={10} />{m.total_score}%
                          </span>
                        </div>
                        <p className="text-xs text-slate-500">{m.explanation}</p>
                        <div className="flex flex-wrap gap-1">
                          {m.matched_required.slice(0, 4).map((s) => <span key={s} className="skill-tag-matched"><CheckCircle2 size={10} />{s}</span>)}
                          {m.missing_required.slice(0, 4).map((s) => <span key={s} className="skill-tag-missing"><XCircle size={10} />{s}</span>)}
                        </div>
                        {next.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {next.map((n) => (
                              <button
                                key={n}
                                disabled={busyApp === it.application_id}
                                onClick={() => void change(it.application_id, n)}
                                className={n === 'rejected' ? 'btn-ghost text-xs py-1 text-red-600' : 'btn-secondary text-xs py-1'}
                              >
                                {n === 'rejected' ? 'Từ chối' : <>Chuyển <ChevronRight size={12} /> {STATUS_LABEL[n]}</>}
                              </button>
                            ))}
                          </div>
                        )}
                      </article>
                    );
                  })}
                  {col.length === 0 && <p className="text-xs text-slate-400 text-center py-3">Chưa có hồ sơ</p>}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
