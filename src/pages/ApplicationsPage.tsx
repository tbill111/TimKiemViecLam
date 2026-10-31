import { useState } from 'react';
import { Bookmark, FileCheck, Eye, Trash2, ChevronDown, Calendar, Building2, Info } from 'lucide-react';
import type { UseAppState } from '../hooks/useAppState';
import type { ApplicationStatus } from '../types';
import { sampleJobs } from '../data/jobs';
import { formatDate, formatRelativeDate } from '../utils';
import JobDetailModal from '../components/jobs/JobDetailModal';
import { calculateSkillMatch } from '../utils';
import type { Job } from '../types';

interface ApplicationsPageProps {
  appState: UseAppState;
}

const statusColors: Record<ApplicationStatus, string> = {
  'Đã ứng tuyển': 'badge-blue',
  'Đang xem xét': 'badge-yellow',
  'Phỏng vấn': 'badge-green',
  'Đã kết thúc': 'badge-gray',
};

const allStatuses: ApplicationStatus[] = ['Đã ứng tuyển', 'Đang xem xét', 'Phỏng vấn', 'Đã kết thúc'];

type Tab = 'saved' | 'applied' | 'tracking';

export default function ApplicationsPage({ appState }: ApplicationsPageProps) {
  const {
    savedJobs,
    applications,
    studentProfile,
    isJobSaved,
    saveJob,
    unsaveJob,
    applyToJob,
    hasApplied,
    updateApplicationStatus,
  } = appState;

  const [activeTab, setActiveTab] = useState<Tab>('saved');
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  const getJob = (jobId: string) => sampleJobs.find((j) => j.id === jobId);

  const savedJobsList = savedJobs
    .map((s) => ({ saved: s, job: getJob(s.jobId) }))
    .filter((x) => x.job !== undefined) as { saved: typeof savedJobs[0]; job: Job }[];

  const appliedList = applications
    .map((a) => ({ app: a, job: getJob(a.jobId) }))
    .filter((x) => x.job !== undefined) as { app: typeof applications[0]; job: Job }[];

  const trackingList = appliedList.filter(
    (x) => x.app.status === 'Đang xem xét' || x.app.status === 'Phỏng vấn'
  );

  const tabs: { id: Tab; label: string; count: number }[] = [
    { id: 'saved', label: 'Đã lưu', count: savedJobsList.length },
    { id: 'applied', label: 'Đã ứng tuyển', count: appliedList.length },
    { id: 'tracking', label: 'Đang theo dõi', count: trackingList.length },
  ];

  const handleOpenDetail = (job: Job) => setSelectedJob(job);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Việc đã lưu & Ứng tuyển</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Quản lý danh sách việc đã lưu và theo dõi tiến trình ứng tuyển demo.
        </p>
      </div>

      <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-100 rounded-xl text-sm text-blue-700">
        <Info size={16} className="shrink-0 mt-0.5" />
        Đây là dữ liệu demo. Trạng thái ứng tuyển chỉ mang tính minh họa, không có thông tin nào được gửi đến nhà tuyển dụng.
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            {tab.label}
            <span className={`text-xs px-1.5 py-0.5 rounded-full ${
              activeTab === tab.id ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500'
            }`}>
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* Tab: Saved */}
      {activeTab === 'saved' && (
        <div>
          {savedJobsList.length === 0 ? (
            <div className="card p-12 text-center">
              <Bookmark size={40} className="mx-auto text-slate-200 mb-3" />
              <h3 className="font-semibold text-slate-500 mb-1">Chưa có việc làm nào được lưu</h3>
              <p className="text-sm text-slate-400">
                Hãy vào trang Tìm việc và nhấn "Lưu việc" để thêm vào danh sách.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {savedJobsList.map(({ saved, job }) => {
                const match = calculateSkillMatch(studentProfile, job);
                return (
                  <div key={saved.jobId} className="card p-4 flex flex-col gap-3">
                    <div className="flex items-start gap-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-slate-800 text-sm">{job.title}</h3>
                        <div className="text-xs text-slate-400">{job.company} · {job.location}</div>
                      </div>
                      <span className={`badge ${match.matchScore >= 70 ? 'badge-green' : match.matchScore >= 50 ? 'badge-blue' : 'badge-gray'}`}>
                        {match.matchScore}%
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Calendar size={12} />
                      Đã lưu {formatRelativeDate(saved.savedAt)}
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => handleOpenDetail(job)} className="btn-secondary text-xs py-1.5 flex-1 justify-center">
                        <Eye size={13} />
                        Xem chi tiết
                      </button>
                      <button onClick={() => unsaveJob(saved.jobId)} className="btn-danger text-xs py-1.5">
                        <Trash2 size={13} />
                        Bỏ lưu
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab: Applied */}
      {activeTab === 'applied' && (
        <div>
          {appliedList.length === 0 ? (
            <div className="card p-12 text-center">
              <FileCheck size={40} className="mx-auto text-slate-200 mb-3" />
              <h3 className="font-semibold text-slate-500 mb-1">Chưa có đơn ứng tuyển nào</h3>
              <p className="text-sm text-slate-400">
                Vào trang Tìm việc, mở chi tiết và nhấn "Ứng tuyển Demo" để bắt đầu.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {appliedList.map(({ app, job }) => (
                <div key={app.id} className="card p-4 flex flex-wrap items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-sm text-slate-800">{job.title}</div>
                    <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                      <Building2 size={11} />
                      {job.company}
                      <span>·</span>
                      <Calendar size={11} />
                      Ứng tuyển {formatDate(app.appliedAt)}
                    </div>
                  </div>

                  {/* Status selector */}
                  <div className="relative">
                    <select
                      value={app.status}
                      onChange={(e) => updateApplicationStatus(app.id, e.target.value as ApplicationStatus)}
                      className={`text-xs font-medium px-3 py-1.5 rounded-lg border appearance-none cursor-pointer pr-7 ${
                        app.status === 'Đã ứng tuyển' ? 'bg-blue-50 text-blue-700 border-blue-100' :
                        app.status === 'Đang xem xét' ? 'bg-amber-50 text-amber-700 border-amber-100' :
                        app.status === 'Phỏng vấn' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' :
                        'bg-slate-50 text-slate-500 border-slate-100'
                      }`}
                    >
                      {allStatuses.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                    <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400" />
                  </div>

                  <button onClick={() => handleOpenDetail(job)} className="btn-ghost text-xs py-1.5">
                    <Eye size={14} />
                    Chi tiết
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab: Tracking */}
      {activeTab === 'tracking' && (
        <div>
          {trackingList.length === 0 ? (
            <div className="card p-12 text-center">
              <Eye size={40} className="mx-auto text-slate-200 mb-3" />
              <h3 className="font-semibold text-slate-500 mb-1">Không có đơn nào đang theo dõi</h3>
              <p className="text-sm text-slate-400">
                Cập nhật trạng thái "Đang xem xét" hoặc "Phỏng vấn" cho đơn đã nộp để theo dõi tại đây.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {trackingList.map(({ app, job }) => (
                <div key={app.id} className={`card p-4 border-l-4 ${app.status === 'Phỏng vấn' ? 'border-l-emerald-500' : 'border-l-amber-400'}`}>
                  <div className="flex items-start gap-3">
                    <div className="flex-1">
                      <div className="font-semibold text-sm text-slate-800">{job.title}</div>
                      <div className="text-xs text-slate-400 mt-0.5">{job.company} · {job.location}</div>
                    </div>
                    <span className={statusColors[app.status]}>
                      {app.status}
                    </span>
                  </div>
                  <div className="mt-2 text-xs text-slate-400">
                    Ngày ứng tuyển: {formatDate(app.appliedAt)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Detail Modal */}
      {selectedJob && (
        <JobDetailModal
          job={selectedJob}
          matchResult={calculateSkillMatch(studentProfile, selectedJob)}
          isSaved={isJobSaved(selectedJob.id)}
          hasApplied={hasApplied(selectedJob.id)}
          onSave={() => isJobSaved(selectedJob.id) ? unsaveJob(selectedJob.id) : saveJob(selectedJob.id)}
          onApply={() => applyToJob(selectedJob.id)}
          onClose={() => setSelectedJob(null)}
        />
      )}
    </div>
  );
}
