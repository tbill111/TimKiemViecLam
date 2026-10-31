import { useState } from 'react';
import {
  X,
  MapPin,
  Briefcase,
  DollarSign,
  CheckCircle2,
  XCircle,
  Bookmark,
  BookmarkCheck,
  Star,
  Clock,
  Building2,
  AlertCircle,
} from 'lucide-react';
import type { Job } from '../../types';
import type { SkillMatchResult } from '../../types';
import { formatRelativeDate, getMatchColorClass } from '../../utils';
import ScoreBreakdown from './ScoreBreakdown';

interface JobDetailModalProps {
  job: Job;
  matchResult: SkillMatchResult;
  isSaved: boolean;
  hasApplied: boolean;
  onSave: () => void;
  onApply: () => void;
  onClose: () => void;
}

export default function JobDetailModal({
  job,
  matchResult,
  isSaved,
  hasApplied,
  onSave,
  onApply,
  onClose,
}: JobDetailModalProps) {
  const [showApplyConfirm, setShowApplyConfirm] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);

  const handleApply = () => {
    if (hasApplied) return;
    setShowApplyConfirm(true);
  };

  const handleConfirmApply = () => {
    onApply();
    setShowApplyConfirm(false);
    setApplySuccess(true);
  };

  const matchColor = getMatchColorClass(matchResult.matchScore);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-start gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <h2 className="text-xl font-bold text-slate-900">{job.title}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <Building2 size={14} className="text-slate-400" />
                  <span className="text-slate-600 font-medium">{job.company}</span>
                  {job.companyIndustry && (
                    <span className="badge-gray text-xs">{job.companyIndustry}</span>
                  )}
                </div>
              </div>
              <div className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-bold ${matchColor}`}>
                <Star size={13} />
                {matchResult.matchScore}% phù hợp
              </div>
            </div>

            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2.5 text-sm text-slate-500">
              <span className="flex items-center gap-1"><MapPin size={13} />{job.location}</span>
              <span className="flex items-center gap-1"><Briefcase size={13} />{job.workType}</span>
              <span className="flex items-center gap-1"><Clock size={13} />{formatRelativeDate(job.postedAt)}</span>
              <span className="flex items-center gap-1 text-emerald-600 font-medium">
                <DollarSign size={13} />{job.salary}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5 shrink-0">
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-5 space-y-5">
          {/* Apply success */}
          {applySuccess && (
            <div className="flex items-center gap-3 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700 text-sm">
              <CheckCircle2 size={18} className="shrink-0" />
              <span>Ứng tuyển thành công! Công việc đã được thêm vào danh sách theo dõi của bạn.</span>
            </div>
          )}

          {/* Apply confirm */}
          {showApplyConfirm && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
              <div className="flex items-start gap-3">
                <AlertCircle size={18} className="text-blue-600 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-blue-800 text-sm">Xác nhận ứng tuyển (Demo)</div>
                  <div className="text-xs text-blue-600 mt-1">
                    Đây là ứng tuyển mô phỏng. Không có dữ liệu thật nào được gửi đến nhà tuyển dụng.
                  </div>
                </div>
              </div>
              <div className="flex gap-2 mt-3">
                <button onClick={handleConfirmApply} className="btn-primary text-xs py-1.5">
                  Xác nhận ứng tuyển
                </button>
                <button onClick={() => setShowApplyConfirm(false)} className="btn-secondary text-xs py-1.5">
                  Hủy
                </button>
              </div>
            </div>
          )}

          {/* Match analysis */}
          <div className="card p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="section-title text-sm">Mức độ phù hợp hồ sơ</h3>
              <span className="text-xs text-slate-400 italic">Mô phỏng ghép nối đa tiêu chí</span>
            </div>
            <ScoreBreakdown result={matchResult} compact />
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div>
                <div className="text-xs font-medium text-emerald-700 mb-1.5 flex items-center gap-1">
                  <CheckCircle2 size={12} />Kỹ năng đã có ({matchResult.matchedSkills.length})
                </div>
                <div className="flex flex-wrap gap-1">
                  {matchResult.matchedSkills.map((s) => (
                    <span key={s} className="skill-tag-matched">{s}</span>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-xs font-medium text-red-700 mb-1.5 flex items-center gap-1">
                  <XCircle size={12} />Kỹ năng còn thiếu ({matchResult.missingSkills.length})
                </div>
                <div className="flex flex-wrap gap-1">
                  {matchResult.missingSkills.map((s) => (
                    <span key={s} className="skill-tag-missing">{s}</span>
                  ))}
                  {matchResult.missingSkills.length === 0 && (
                    <span className="text-xs text-slate-400">Bạn đáp ứng đầy đủ yêu cầu!</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <h3 className="section-title text-sm mb-2">Mô tả công việc</h3>
            <p className="text-sm text-slate-600 leading-relaxed">{job.description}</p>
          </div>

          {/* Responsibilities */}
          <div>
            <h3 className="section-title text-sm mb-2">Trách nhiệm chính</h3>
            <ul className="space-y-1.5">
              {job.responsibilities.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-2 shrink-0" />
                  {r}
                </li>
              ))}
            </ul>
          </div>

          {/* Required Skills */}
          <div>
            <h3 className="section-title text-sm mb-2">Kỹ năng yêu cầu</h3>
            <div className="flex flex-wrap gap-1.5">
              {job.requiredSkills.map((s) => (
                <span key={s} className="skill-tag">{s}</span>
              ))}
            </div>
          </div>

          {/* Preferred Skills */}
          {job.preferredSkills.length > 0 && (
            <div>
              <h3 className="section-title text-sm mb-2">Kỹ năng ưu tiên</h3>
              <div className="flex flex-wrap gap-1.5">
                {job.preferredSkills.map((s) => (
                  <span key={s} className="badge-gray">{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Company Info */}
          {job.companySize && (
            <div className="card p-4 bg-slate-50">
              <h3 className="section-title text-sm mb-2">Thông tin tuyển dụng</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-slate-400">Quy mô:</span> <span className="font-medium">{job.companySize}</span></div>
                <div><span className="text-slate-400">Lĩnh vực:</span> <span className="font-medium">{job.companyIndustry}</span></div>
                <div><span className="text-slate-400">Kinh nghiệm:</span> <span className="font-medium">{job.experienceLevel}</span></div>
              </div>
              <p className="text-xs text-slate-400 italic mt-2">* Thông tin chỉ mang tính minh họa trong prototype.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex items-center gap-3">
          <button
            onClick={handleApply}
            disabled={hasApplied}
            className={`btn-primary ${hasApplied ? 'opacity-60 cursor-not-allowed' : ''}`}
          >
            {hasApplied ? (
              <>
                <CheckCircle2 size={16} />
                Đã ứng tuyển
              </>
            ) : (
              'Ứng tuyển Demo'
            )}
          </button>
          <button
            onClick={onSave}
            className={`btn-secondary ${isSaved ? 'border-emerald-200 text-emerald-600 bg-emerald-50' : ''}`}
          >
            {isSaved ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}
            {isSaved ? 'Đã lưu' : 'Lưu việc làm'}
          </button>
          <span className="ml-auto text-xs text-slate-400 italic">Dữ liệu mẫu minh họa</span>
        </div>
      </div>
    </div>
  );
}
