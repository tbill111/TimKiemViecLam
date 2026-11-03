import { useEffect, useState } from 'react';
import { fetchEmployerJobs, fetchRankedCandidates, moveApplication, type RankedCandidate } from '../api/employer';
import { isOfflineDemo, apiErrorMessage } from '../api/client';
import { demoRankedCandidates } from '../api/demoEmployer';
import { sampleJobs } from '../data/jobs';
import type { ApplicationStatus, Job } from '../types';
import LoadingBlock from '../components/ui/LoadingBlock';
import ErrorBlock from '../components/ui/ErrorBlock';
import EmptyBlock from '../components/ui/EmptyBlock';

const columns: Array<{ status: ApplicationStatus; api: string }> = [
  { status: 'Đã ứng tuyển', api: 'applied' }, { status: 'Đang xem xét', api: 'screening' }, { status: 'Phỏng vấn', api: 'interview' },
  { status: 'Đề nghị nhận việc', api: 'offer' }, { status: 'Đã nhận việc', api: 'hired' }, { status: 'Đã từ chối', api: 'rejected' },
];
const labels: Record<string, ApplicationStatus> = { applied: 'Đã ứng tuyển', screening: 'Đang xem xét', interview: 'Phỏng vấn', offer: 'Đề nghị nhận việc', hired: 'Đã nhận việc', rejected: 'Đã từ chối' };
const allowedNext: Partial<Record<ApplicationStatus, ApplicationStatus[]>> = {
  'Đã ứng tuyển': ['Đang xem xét', 'Đã từ chối'],
  'Đang xem xét': ['Phỏng vấn', 'Đã từ chối'],
  'Phỏng vấn': ['Đề nghị nhận việc', 'Đã từ chối'],
  'Đề nghị nhận việc': ['Đã nhận việc', 'Đã từ chối'],
};

export default function EmployerKanbanPage() {
  const [jobs, setJobs] = useState<Job[]>(isOfflineDemo ? sampleJobs : []);
  const [jobId, setJobId] = useState('');
  const [items, setItems] = useState<RankedCandidate[]>([]);
  const [loading, setLoading] = useState(!isOfflineDemo);
  const [error, setError] = useState('');
  const load = async (id: string) => { if (!id) return; if (isOfflineDemo) { const demoJob = jobs.find((job) => job.id === id); setItems(demoJob ? demoRankedCandidates(demoJob) : []); return; } setLoading(true); try { setItems(await fetchRankedCandidates(id)); } catch (e) { setError(apiErrorMessage(e, 'Không tải được ứng viên.')); } finally { setLoading(false); } };
  useEffect(() => { if (!isOfflineDemo) void fetchEmployerJobs().then(setJobs).catch((e) => setError(apiErrorMessage(e, 'Không tải được tin tuyển dụng.'))); }, []);
  useEffect(() => { if (!jobId && jobs[0]) setJobId(jobs[0].id); }, [jobId, jobs]);
  useEffect(() => { void load(jobId); }, [jobId]);
  const move = async (item: RankedCandidate, status: ApplicationStatus) => { if (isOfflineDemo) { const target = columns.find((column) => column.status === status); if (target) setItems((previous) => previous.map((entry) => entry.application_id === item.application_id ? { ...entry, status: target.api } : entry)); return; } try { await moveApplication(item.application_id, status); await load(jobId); } catch (e) { setError(apiErrorMessage(e, 'Chuyển trạng thái không hợp lệ.')); } };
  return <div className="space-y-5"><div><h1 className="text-2xl font-bold">Kanban tuyển dụng</h1><p className="section-subtitle">Quản lý trạng thái ứng viên theo đúng quy trình</p></div><select className="select-field max-w-xl" value={jobId} onChange={(e) => setJobId(e.target.value)}>{jobs.map((job) => <option key={job.id} value={job.id}>{job.title}</option>)}</select>{error && <ErrorBlock message={error} onRetry={() => void load(jobId)} />}{loading ? <LoadingBlock message="Đang tải Kanban..." /> : items.length === 0 ? <EmptyBlock message="Chưa có ứng viên đã nộp vào tin này." /> : <div className="grid grid-cols-1 gap-3 md:grid-cols-3 xl:grid-cols-6">{columns.map((column) => <section className="min-h-48 rounded-xl bg-slate-100 p-3" key={column.status}><h2 className="mb-3 text-sm font-semibold">{column.status}</h2>{items.filter((item) => (labels[item.status] ?? 'Đã ứng tuyển') === column.status).map((item) => <article className="card mb-2 p-3" key={item.application_id}><strong className="text-sm">{item.full_name}</strong><div className="mt-1 text-xs text-blue-600">{Math.round(item.match.total_score)}% phù hợp</div><p className="mt-1 text-xs text-slate-500">{item.match.explanation}</p><div className="mt-2 flex flex-wrap gap-1">{(allowedNext[column.status] ?? []).map((next) => <button className="btn-secondary text-xs" key={next} onClick={() => void move(item, next)}>{next === 'Đã từ chối' ? 'Từ chối' : `→ ${next}`}</button>)}</div></article>)}</section>)}</div>}</div>;
}
