import { MapPin, Clock, Bookmark, BookmarkCheck, ChevronRight, Star } from 'lucide-react';
import type { Job } from '../../types';
import type { SkillMatchResult } from '../../types';
import { formatRelativeDate, getMatchColorClass } from '../../utils';

interface JobCardProps {
  job: Job;
  matchResult: SkillMatchResult;
  isSaved: boolean;
  onSave: () => void;
  onViewDetail: () => void;
}

const workTypeBadgeClass: Record<string, string> = {
  'Toàn thời gian': 'badge-blue',
  'Bán thời gian': 'badge-yellow',
  'Thực tập': 'badge-purple',
  'Remote': 'badge-green',
};

export default function JobCard({ job, matchResult, isSaved, onSave, onViewDetail }: JobCardProps) {
  return (
    <div className="card-hover p-5 flex flex-col gap-3 cursor-default">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3
            className="font-semibold text-slate-800 text-base leading-snug hover:text-blue-600 cursor-pointer transition-colors"
            onClick={onViewDetail}
          >
            {job.title}
          </h3>
          <div className="text-sm text-slate-500 mt-0.5">{job.company}</div>
        </div>

        {/* Match score */}
        <div
          className={`shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${getMatchColorClass(matchResult.matchScore)}`}
        >
          <Star size={11} />
          {matchResult.matchScore}%
        </div>
      </div>

      {/* Meta */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <MapPin size={12} />
          {job.location}
        </span>
        <span className="flex items-center gap-1">
          <Clock size={12} />
          {formatRelativeDate(job.postedAt)}
        </span>
        <span className={workTypeBadgeClass[job.workType] ?? 'badge-gray'}>
          {job.workType}
        </span>
        <span className="badge-gray">{job.experienceLevel}</span>
      </div>

      {/* Salary */}
      <div className="text-sm font-medium text-emerald-600">{job.salary.trim() || 'Thỏa thuận'}</div>

      {/* Skills */}
      <div className="flex flex-wrap gap-1.5">
        {job.requiredSkills.slice(0, 4).map((skill) => {
          const matched = matchResult.matchedSkills.some(
            (s) => s.toLowerCase() === skill.toLowerCase()
          );
          return (
            <span
              key={skill}
              className={matched ? 'skill-tag-matched' : 'skill-tag'}
            >
              {skill}
            </span>
          );
        })}
        {job.requiredSkills.length > 4 && (
          <span className="badge-gray">+{job.requiredSkills.length - 4}</span>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1">
        <button onClick={onViewDetail} className="btn-primary text-xs py-1.5">
          Xem chi tiết
          <ChevronRight size={14} />
        </button>
        <button
          onClick={onSave}
          className={`btn-secondary text-xs py-1.5 ${isSaved ? 'border-emerald-200 text-emerald-600 bg-emerald-50 hover:bg-emerald-100' : ''}`}
        >
          {isSaved ? (
            <>
              <BookmarkCheck size={14} />
              Đã lưu
            </>
          ) : (
            <>
              <Bookmark size={14} />
              Lưu việc làm
            </>
          )}
        </button>
      </div>
    </div>
  );
}
