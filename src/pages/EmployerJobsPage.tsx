import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Job } from '../types';
import { fetchEmployerJobs, closeJob } from '../api/employer';
import { isOfflineDemo, apiErrorMessage } from '../api/client';
import LoadingBlock from '../components/ui/LoadingBlock';
import ErrorBlock from '../components/ui/ErrorBlock';
import EmptyBlock from '../components/ui/EmptyBlock';
import { sampleJobs } from '../data/jobs';

export default function EmployerJobsPage() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>(isOfflineDemo ? sampleJobs : []);
  const [loading, setLoading] = useState(!isOfflineDemo);
  const [error, setError] = useState('');
  const load = async () => {
    if (isOfflineDemo) return;
    setLoading(true);
    try { setJobs(await fetchEmployerJobs()); }
    catch (e) { setError(apiErrorMessage(e, 'Không tải được tin tuyển dụng.')); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);
  const handleClose = async (id: string) => {
    if (isOfflineDemo || !window.confirm('Đóng tin tuyển dụng này?')) return;
    try { await closeJob(id); await load(); }
    catch (e) { setError(apiErrorMessage(e, 'Không đóng được tin.')); }
  };
  return <div className="space-y-5"><div className="flex justify-between"><div><h1 className="text-2xl font-bold">Quản lý tin tuyển dụng</h1><p className="section-subtitle">Danh sách tin của công ty</p></div><a className="btn-primary" href="/employer/jobs/new">Đăng tin mới</a></div>{loading ? <LoadingBlock message="Đang tải tin tuyển dụng..." /> : error ? <ErrorBlock message={error} onRetry={() => void load()} /> : jobs.length === 0 ? <EmptyBlock message="Công ty chưa có tin tuyển dụng." /> : <div className="space-y-3">{jobs.map((job) => <div className="card p-4 flex justify-between gap-4" key={job.id}><div><h2 className="font-semibold">{job.title}</h2><p className="text-sm text-slate-500">{job.location} · {job.workType} · {job.salary}</p></div><div className="flex gap-2"><button className="btn-secondary" onClick={() => navigate(`/employer/jobs/${job.id}/edit`)}>Sửa</button><button className="btn-danger" onClick={() => void handleClose(job.id)}>Đóng tin</button></div></div>)}</div>}</div>;
}
