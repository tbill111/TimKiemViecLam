import { useEffect, useState } from 'react';
import { fetchEmployerJobs, fetchRankedCandidates, type RankedCandidate } from '../api/employer';
import { isOfflineDemo, apiErrorMessage } from '../api/client';
import { demoRankedCandidates } from '../api/demoEmployer';
import { sampleJobs } from '../data/jobs';
import type { Job } from '../types';
import LoadingBlock from '../components/ui/LoadingBlock';
import ErrorBlock from '../components/ui/ErrorBlock';
import EmptyBlock from '../components/ui/EmptyBlock';

export default function EmployerCandidatesPage() {
  const [jobs, setJobs] = useState<Job[]>(isOfflineDemo ? sampleJobs : []);
  const [jobId, setJobId] = useState('');
  const [items, setItems] = useState<RankedCandidate[]>([]);
  const [loading, setLoading] = useState(!isOfflineDemo);
  const [error, setError] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState<RankedCandidate | null>(null);
  const loadCandidates = async (id: string) => {
    if (!id) return;
    if (isOfflineDemo) {
      const demoJob = jobs.find((job) => job.id === id);
      setItems(demoJob ? demoRankedCandidates(demoJob) : []);
      return;
    }
    setLoading(true);
    try { setItems((await fetchRankedCandidates(id)).sort((a, b) => b.match.total_score - a.match.total_score)); }
    catch (e) { setError(apiErrorMessage(e, 'Không tải được ứng viên.')); }
    finally { setLoading(false); }
  };
  useEffect(() => { if (!isOfflineDemo) void fetchEmployerJobs().then(setJobs).catch((e) => setError(apiErrorMessage(e, 'Không tải được tin tuyển dụng.'))); }, []);
  useEffect(() => { if (!jobId && jobs[0]) setJobId(jobs[0].id); }, [jobId, jobs]);
  useEffect(() => { void loadCandidates(jobId); }, [jobId]);
  useEffect(() => {
    if (!selectedCandidate) return;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') setSelectedCandidate(null); };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [selectedCandidate]);
  return <div className="space-y-5"><div><h1 className="text-2xl font-bold">Ứng viên xếp hạng</h1><p className="section-subtitle">Ứng viên được xếp theo điểm khớp giảm dần</p></div><select className="select-field max-w-xl" value={jobId} onChange={(e) => setJobId(e.target.value)}>{jobs.map((job) => <option key={job.id} value={job.id}>{job.title}</option>)}</select>{error && <ErrorBlock message={error} onRetry={() => void loadCandidates(jobId)} />}{loading ? <LoadingBlock message="Đang tải ứng viên..." /> : items.length === 0 ? <EmptyBlock message="Chưa có ứng viên đã nộp vào tin này." /> : <div className="space-y-3">{items.map((item, index) => <article className="card p-4" key={item.application_id}><div className="flex items-start gap-3"><div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-700">{index + 1}</div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-start justify-between gap-2"><div><h2 className="font-semibold">{item.full_name}</h2><span className="font-bold text-blue-600">{Math.round(item.match.total_score)}% phù hợp</span></div><button className="btn-secondary" type="button" onClick={() => setSelectedCandidate(item)}>Chi tiết</button></div><p className="mt-1 text-sm text-slate-600">{item.match.explanation || 'Chưa có lý do khớp chi tiết.'}</p><div className="mt-2 grid gap-2 text-xs md:grid-cols-2"><div><strong className="text-emerald-700">Kỹ năng phù hợp:</strong> {item.match.matched_required.join(', ') || 'Chưa có'}</div><div><strong className="text-red-700">Kỹ năng còn thiếu:</strong> {item.match.missing_required.join(', ') || 'Không có'}</div></div></div></div></article>)}</div>}{selectedCandidate && <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4" role="dialog" aria-modal="true" aria-labelledby="candidate-detail-title"><div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl"><div className="flex items-start justify-between gap-4"><div><h2 id="candidate-detail-title" className="text-xl font-bold">Chi tiết ứng viên</h2><p className="text-sm text-slate-500">{selectedCandidate.full_name}</p></div><button type="button" className="btn-secondary" aria-label="Đóng" onClick={() => setSelectedCandidate(null)}>Đóng</button></div><div className="mt-5 grid gap-4 md:grid-cols-2"><div className="rounded-lg bg-blue-50 p-4"><div className="text-sm text-slate-600">Điểm khớp tổng hợp</div><div className="text-2xl font-bold text-blue-700">{Math.round(selectedCandidate.match.total_score)}%</div></div><div className="rounded-lg bg-slate-50 p-4"><div className="text-sm text-slate-600">Ngày ứng tuyển</div><div className="font-semibold">{new Date(`${selectedCandidate.applied_at}Z`).toLocaleString('vi-VN')}</div></div></div><div className="mt-5 space-y-4 text-sm"><div><h3 className="font-semibold text-slate-800">Lý do khớp</h3><p className="mt-1 text-slate-600">{selectedCandidate.match.explanation || 'Chưa có lý do khớp chi tiết.'}</p></div><div><h3 className="font-semibold text-emerald-700">Kỹ năng phù hợp</h3><p className="mt-1 text-slate-600">{selectedCandidate.match.matched_required.join(', ') || 'Chưa có kỹ năng phù hợp.'}</p></div><div><h3 className="font-semibold text-red-700">Kỹ năng còn thiếu</h3><p className="mt-1 text-slate-600">{selectedCandidate.match.missing_required.join(', ') || 'Không thiếu kỹ năng bắt buộc.'}</p></div></div><p className="mt-5 rounded-lg bg-amber-50 p-3 text-xs text-amber-800">Chi tiết CV đầy đủ sẽ hiển thị khi backend cung cấp endpoint hồ sơ ứng viên; hiện API xếp hạng chỉ trả các thông tin trên.</p></div></div>}</div>;
}
