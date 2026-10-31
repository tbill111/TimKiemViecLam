import { useMemo, useState } from 'react';
import { Building2, Info, Users, Star, Send, CheckCircle2, XCircle } from 'lucide-react';
import type { UseAppState } from '../hooks/useAppState';
import type { ApplicationStatus, Candidate, SkillMatchResult } from '../types';
import { sampleJobs } from '../data/jobs';
import { sampleCandidates } from '../data/candidates';
import { calculateSkillMatch, getMatchColorClass, SUITABLE_THRESHOLD } from '../utils';
import ScoreBreakdown from '../components/jobs/ScoreBreakdown';

interface EmployerPageProps {
  appState: UseAppState;
}

const STUDENT_ID = 'me';
const allStatuses: ApplicationStatus[] = ['Đã ứng tuyển', 'Đang xem xét', 'Phỏng vấn', 'Đã kết thúc'];

interface RankedCandidate {
  candidate: Candidate;
  result: SkillMatchResult;
  isStudent: boolean;
}

const initials = (name: string) =>
  name
    .split(' ')
    .slice(-2)
    .map((n) => n[0])
    .join('');

export default function EmployerPage({ appState }: EmployerPageProps) {
  const { studentProfile, applications, updateApplicationStatus } = appState;

  // Mặc định mở tin mà sinh viên đã ứng tuyển gần nhất, nếu có
  const defaultJobId = applications.at(-1)?.jobId ?? 'job-011';
  const [jobId, setJobId] = useState(defaultJobId);
  const [invited, setInvited] = useState<Set<string>>(new Set());

  const job = sampleJobs.find((j) => j.id === jobId) ?? sampleJobs[0];
  const application = applications.find((a) => a.jobId === job.id);

  const ranked = useMemo<RankedCandidate[]>(() => {
    const student: Candidate = {
      id: STUDENT_ID,
      fullName: studentProfile.fullName,
      major: studentProfile.major,
      university: studentProfile.university,
      year: studentProfile.year,
      skills: studentProfile.skills,
      preferredLocations: studentProfile.preferredLocations,
      preferredWorkTypes: studentProfile.preferredWorkTypes,
    };
    return [student, ...sampleCandidates]
      .map((candidate) => ({ candidate, result: calculateSkillMatch(candidate, job), isStudent: candidate.id === STUDENT_ID }))
      .sort((a, b) => b.result.matchScore - a.result.matchScore);
  }, [studentProfile, job]);

  const suitable = ranked.filter((r) => r.result.matchScore >= SUITABLE_THRESHOLD).length;

  const invite = (id: string) => setInvited((prev) => new Set(prev).add(id));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Cổng nhà tuyển dụng</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Góc nhìn doanh nghiệp: ứng viên được xếp hạng theo mức phù hợp với tin tuyển dụng.
        </p>
      </div>

      <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-100 rounded-xl text-sm text-blue-700">
        <Info size={16} className="shrink-0 mt-0.5" />
        <span>
          Mô phỏng phía nhà tuyển dụng. {sampleCandidates.length} ứng viên mẫu là dữ liệu minh họa; hồ sơ của bạn được
          đưa vào để thấy kết nối hai chiều. Trạng thái cập nhật ở đây sẽ hiện ở trang "Việc đã lưu & Ứng tuyển".
        </span>
      </div>

      {/* Chọn tin tuyển dụng */}
      <div className="card p-5 flex flex-col md:flex-row md:items-end gap-4">
        <div className="flex-1 min-w-0">
          <label htmlFor="employer-job" className="block text-xs font-medium text-slate-500 mb-1.5">
            Tin tuyển dụng của doanh nghiệp
          </label>
          <select id="employer-job" className="select-field" value={job.id} onChange={(e) => setJobId(e.target.value)}>
            {sampleJobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title} – {j.company}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-6 text-sm">
          <div>
            <div className="text-xs text-slate-400 flex items-center gap-1"><Users size={12} />Ứng viên</div>
            <div className="text-xl font-bold text-slate-900">{ranked.length}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400 flex items-center gap-1"><Star size={12} />Từ {SUITABLE_THRESHOLD}%</div>
            <div className="text-xl font-bold text-emerald-600">{suitable}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400 flex items-center gap-1"><Send size={12} />Đã ứng tuyển</div>
            <div className="text-xl font-bold text-blue-600">{application ? 1 : 0}</div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Building2 size={14} />
        {job.company} · {job.location} · {job.workType} · Yêu cầu: {job.requiredSkills.join(', ')}
      </div>

      {/* Danh sách ứng viên xếp hạng */}
      <div className="space-y-3">
        {ranked.map(({ candidate, result, isStudent }, index) => (
          <div
            key={candidate.id}
            className={`card p-4 grid grid-cols-1 lg:grid-cols-[1fr_220px_200px] gap-4 ${isStudent ? 'border-blue-300 bg-blue-50/40' : ''}`}
          >
            {/* Thông tin ứng viên */}
            <div className="flex gap-3 min-w-0">
              <div className="w-7 text-center text-sm font-bold text-slate-400 pt-2">#{index + 1}</div>
              <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-700 font-bold text-sm shrink-0">
                {initials(candidate.fullName)}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-slate-800 text-sm">{candidate.fullName}</span>
                  {isStudent ? (
                    <span className="badge-blue">Hồ sơ của bạn</span>
                  ) : (
                    <span className="badge-gray">Ứng viên mẫu</span>
                  )}
                </div>
                <div className="text-xs text-slate-500">
                  {candidate.major} · {candidate.university} · {candidate.year}
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {result.matchedSkills.map((s) => (
                    <span key={s} className="skill-tag-matched"><CheckCircle2 size={10} />{s}</span>
                  ))}
                  {result.missingSkills.map((s) => (
                    <span key={s} className="skill-tag-missing"><XCircle size={10} />{s}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* Điểm */}
            <div>
              <div className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold mb-2 ${getMatchColorClass(result.matchScore)}`}>
                <Star size={11} />
                {result.matchScore}% phù hợp
              </div>
              <ScoreBreakdown result={result} compact />
            </div>

            {/* Hành động */}
            <div className="flex flex-col justify-center gap-2">
              {isStudent ? (
                application ? (
                  <>
                    <label htmlFor="student-status" className="text-xs text-slate-500">Trạng thái hồ sơ</label>
                    <select
                      id="student-status"
                      className="select-field text-xs"
                      value={application.status}
                      onChange={(e) => updateApplicationStatus(application.id, e.target.value as ApplicationStatus)}
                    >
                      {allStatuses.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </>
                ) : (
                  <p className="text-xs text-slate-500">
                    Chưa ứng tuyển vị trí này. Ứng tuyển ở trang Tìm việc để nhà tuyển dụng cập nhật trạng thái.
                  </p>
                )
              ) : invited.has(candidate.id) ? (
                <span className="text-xs font-medium text-emerald-600 flex items-center gap-1">
                  <CheckCircle2 size={14} />
                  Đã gửi lời mời (demo)
                </span>
              ) : (
                <button onClick={() => invite(candidate.id)} className="btn-secondary text-xs py-1.5 justify-center">
                  <Send size={13} />
                  Mời phỏng vấn
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
