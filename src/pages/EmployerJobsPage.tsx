import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Building2, MapPin, Pencil, PlusCircle, Users, XCircle } from 'lucide-react';
import { jobsApi } from '../api/endpoints';
import { toJob } from '../api/adapters';
import { errorMessage } from '../api/client';
import type { Job } from '../types';
import { formatDate } from '../utils';
import LoadingBlock from '../components/ui/LoadingBlock';
import ErrorBlock from '../components/ui/ErrorBlock';
import EmptyBlock from '../components/ui/EmptyBlock';

/** Quản lý tin tuyển dụng của công ty: xem, sửa, đóng tin. */
export default function EmployerJobsPage() {
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    jobsApi
      .list({ mine: true, sort: 'newest' })
      .then((r) => setJobs(r.items.map(toJob)))
      .catch((e) => setError(errorMessage(e)));
  }, []);

  useEffect(load, [load]);

  const close = async (job: Job) => {
    if (!window.confirm(`Đóng tin "${job.title}"? Tin sẽ không còn hiển thị cho ứng viên, hồ sơ đã nộp vẫn được giữ.`)) return;
    setBusyId(job.id);
    try {
      await jobsApi.close(job.id);
      load();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Quản lý tin tuyển dụng</h1>
          <p className="text-slate-500 text-sm mt-0.5">Các tin của công ty bạn, kể cả tin đã đóng.</p>
        </div>
        <Link to="/employer/jobs/new" className="btn-primary text-sm">
          <PlusCircle size={15} />
          Đăng tin mới
        </Link>
      </div>

      {error && <ErrorBlock message={error} onRetry={load} />}
      {!jobs && !error && <LoadingBlock rows={3} message="Đang tải tin tuyển dụng..." />}
      {jobs && jobs.length === 0 && (
        <EmptyBlock title="Công ty chưa có tin tuyển dụng" hint="Đăng tin đầu tiên để bắt đầu nhận hồ sơ." action={<Link to="/employer/jobs/new" className="btn-primary text-sm">Đăng tin</Link>} />
      )}

      {jobs && jobs.length > 0 && (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div key={job.id} className="card p-4 flex flex-wrap items-center gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-slate-800">{job.title}</span>
                  <span className={job.status === 'open' ? 'badge-green' : 'badge-gray'}>{job.status === 'open' ? 'Đang mở' : 'Đã đóng'}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500 mt-1 flex-wrap">
                  <Building2 size={12} />{job.company}
                  <MapPin size={12} />{job.location} · {job.workType} · {job.salary}
                </div>
                <div className="text-xs text-slate-400 mt-1">Đăng {formatDate(job.postedAt)} · Bắt buộc: {job.requiredSkills.join(', ') || '—'}</div>
              </div>
              <div className="flex gap-2">
                <Link to={`/employer/candidates?job=${job.id}`} className="btn-secondary text-xs py-1.5">
                  <Users size={13} />
                  Ứng viên
                </Link>
                <Link to={`/employer/jobs/${job.id}/edit`} className="btn-secondary text-xs py-1.5">
                  <Pencil size={13} />
                  Sửa
                </Link>
                {job.status === 'open' && (
                  <button onClick={() => void close(job)} disabled={busyId === job.id} className="btn-ghost text-xs py-1.5 text-red-600">
                    <XCircle size={13} />
                    Đóng tin
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
