import { useMemo, useState } from 'react';
import { CheckCircle2, Circle, ChevronDown, ChevronUp, Target, Info } from 'lucide-react';
import type { UseAppState } from '../hooks/useAppState';
import type { Job, SkillPriority, StudentProfile } from '../types';
import { sampleJobs } from '../data/jobs';
import { buildLearningSteps } from '../data/skillGap';
import { calculateSkillMatch, hasSkill } from '../utils';

interface SkillGapPageProps {
  appState: UseAppState;
}

interface SkillGapRow {
  skill: string;
  priority: SkillPriority;
}

type PriorityFilter = SkillPriority | 'Tất cả';

const priorityColor: Record<SkillPriority, string> = {
  'Cao': 'badge-red',
  'Trung bình': 'badge-yellow',
  'Thấp': 'badge-gray',
};

const priorityBg: Record<SkillPriority, string> = {
  'Cao': 'bg-red-50 border-red-100',
  'Trung bình': 'bg-amber-50 border-amber-100',
  'Thấp': 'bg-slate-50 border-slate-100',
};

const normalize = (s: string) => s.trim().toLowerCase();

/** Công việc mục tiêu mặc định: công việc có nhiều kỹ năng bắt buộc còn thiếu nhất. */
function findDefaultTarget(profile: StudentProfile): Job {
  return sampleJobs.reduce((best, job) => {
    const missing = calculateSkillMatch(profile, job).missingSkills.length;
    const bestMissing = calculateSkillMatch(profile, best).missingSkills.length;
    return missing > bestMissing ? job : best;
  });
}

/** Kỹ năng còn thiếu của công việc: bắt buộc (Cao) và ưu tiên (Trung bình) chưa có trong hồ sơ. */
function buildGapRows(profile: StudentProfile, job: Job): SkillGapRow[] {
  const required = calculateSkillMatch(profile, job).missingSkills.map((skill) => ({
    skill,
    priority: 'Cao' as const,
  }));
  const preferred = job.preferredSkills
    .filter((skill) => !hasSkill(profile.skills, skill))
    .map((skill) => ({ skill, priority: 'Trung bình' as const }));
  return [...required, ...preferred];
}

export default function SkillGapPage({ appState }: SkillGapPageProps) {
  const { skillGapItems, toggleSkillLearned, updateSkillGapItems, studentProfile } = appState;
  const [targetId, setTargetId] = useState<string | null>(null);
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null);
  const [filterPriority, setFilterPriority] = useState<PriorityFilter>('Tất cả');

  const defaultTarget = useMemo(() => findDefaultTarget(studentProfile), [studentProfile]);
  const target = sampleJobs.find((j) => j.id === targetId) ?? defaultTarget;
  const targetMatch = calculateSkillMatch(studentProfile, target);

  const gapRows = useMemo(() => buildGapRows(studentProfile, target), [studentProfile, target]);

  const findGapItem = (skill: string) => skillGapItems.find((i) => normalize(i.skill) === normalize(skill));
  const isLearned = (skill: string) => findGapItem(skill)?.learned ?? false;

  const toggleLearned = (row: SkillGapRow) => {
    const existing = findGapItem(row.skill);
    if (existing) {
      toggleSkillLearned(existing.id);
      return;
    }
    // Kỹ năng chưa có trong danh mục: tạo mục mới ở trạng thái đã học
    updateSkillGapItems([
      ...skillGapItems,
      {
        id: `gap-custom-${normalize(row.skill).replace(/\s+/g, '-')}`,
        skill: row.skill,
        priority: row.priority,
        category: target.category,
        learned: true,
        learningSteps: buildLearningSteps(row.skill),
      },
    ]);
  };

  const learnedCount = gapRows.filter((r) => isLearned(r.skill)).length;
  const total = gapRows.length;
  const progress = total > 0 ? Math.round((learnedCount / total) * 100) : 100;
  const highPending = gapRows.filter((r) => r.priority === 'Cao' && !isLearned(r.skill)).length;
  const midPending = gapRows.filter((r) => r.priority === 'Trung bình' && !isLearned(r.skill)).length;

  const displayed = filterPriority === 'Tất cả' ? gapRows : gapRows.filter((r) => r.priority === filterPriority);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Skill Gap Analysis</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Phân tích khoảng trống kỹ năng cho công việc mục tiêu và theo dõi tiến độ học.
        </p>
      </div>

      <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-100 rounded-xl text-sm text-blue-700">
        <Info size={16} className="shrink-0 mt-0.5" />
        <span>
          Kỹ năng còn thiếu được tính bằng cách so sánh hồ sơ của bạn với yêu cầu của công việc mục tiêu.
          Trạng thái "đã học" được lưu trên trình duyệt này.
        </span>
      </div>

      {/* Target job */}
      <div className="card p-5 flex flex-col md:flex-row md:items-center gap-4">
        <div className="flex-1 min-w-0">
          <label htmlFor="target-job" className="block text-xs font-medium text-slate-500 mb-1.5">
            Công việc mục tiêu
          </label>
          <select
            id="target-job"
            className="select-field"
            value={target.id}
            onChange={(e) => {
              setTargetId(e.target.value);
              setExpandedSkill(null);
            }}
          >
            {sampleJobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title} – {job.company}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-6 text-sm">
          <div>
            <div className="text-xs text-slate-400">Mức phù hợp hiện tại</div>
            <div className="text-xl font-bold text-slate-900">{targetMatch.matchScore}%</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Kỹ năng bắt buộc còn thiếu</div>
            <div className="text-xl font-bold text-red-500">{targetMatch.missingSkills.length}</div>
          </div>
        </div>
      </div>

      {/* Overview stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="text-xs text-slate-400 uppercase tracking-wide">Tiến độ học</div>
          <div className="text-3xl font-bold text-slate-900">{progress}%</div>
          <div className="progress-bar mt-1">
            <div className="progress-fill bg-emerald-500" style={{ width: `${progress}%` }} />
          </div>
        </div>
        <div className="stat-card">
          <div className="text-xs text-slate-400 uppercase tracking-wide">Đã học</div>
          <div className="text-3xl font-bold text-emerald-600">{learnedCount}</div>
          <div className="text-xs text-slate-400">/ {total} kỹ năng cần có</div>
        </div>
        <div className="stat-card">
          <div className="text-xs text-slate-400 uppercase tracking-wide">Ưu tiên cao</div>
          <div className="text-3xl font-bold text-red-500">{highPending}</div>
          <div className="text-xs text-slate-400">Chưa học, cần học gấp</div>
        </div>
        <div className="stat-card">
          <div className="text-xs text-slate-400 uppercase tracking-wide">Ưu tiên trung bình</div>
          <div className="text-3xl font-bold text-amber-500">{midPending}</div>
          <div className="text-xs text-slate-400">Chưa học, nên học tiếp</div>
        </div>
      </div>

      {/* Current skills */}
      <div className="card p-5">
        <h2 className="section-title text-sm mb-3">Kỹ năng hiện có của bạn</h2>
        <div className="flex flex-wrap gap-1.5">
          {studentProfile.skills.map((s) => (
            <span key={s} className="skill-tag-matched">
              <CheckCircle2 size={11} />
              {s}
            </span>
          ))}
        </div>
      </div>

      {/* Gap items */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
          <h2 className="section-title">Kỹ năng cần phát triển</h2>
          <div className="flex flex-wrap gap-2">
            {(['Tất cả', 'Cao', 'Trung bình'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setFilterPriority(p)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                  filterPriority === p
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          {displayed.map((row) => {
            const learned = isLearned(row.skill);
            const expanded = expandedSkill === row.skill;
            const steps = findGapItem(row.skill)?.learningSteps ?? buildLearningSteps(row.skill);
            return (
              <div
                key={row.skill}
                className={`card border overflow-hidden transition-all ${learned ? 'opacity-60' : ''} ${priorityBg[row.priority]}`}
              >
                <div className="p-4 flex items-center gap-4">
                  <button
                    onClick={() => toggleLearned(row)}
                    className="shrink-0 transition-transform active:scale-95"
                    title={learned ? 'Đánh dấu chưa học' : 'Đánh dấu đã học'}
                    aria-label={learned ? `Đánh dấu chưa học: ${row.skill}` : `Đánh dấu đã học: ${row.skill}`}
                  >
                    {learned ? (
                      <CheckCircle2 size={22} className="text-emerald-500" />
                    ) : (
                      <Circle size={22} className="text-slate-300 hover:text-blue-400 transition-colors" />
                    )}
                  </button>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`font-semibold text-sm ${learned ? 'line-through text-slate-400' : 'text-slate-800'}`}>
                        {row.skill}
                      </span>
                      <span className={priorityColor[row.priority]}>
                        Ưu tiên {row.priority}
                      </span>
                      {learned && <span className="badge-green">Đã học</span>}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      {row.priority === 'Cao' ? 'Yêu cầu bắt buộc' : 'Kỹ năng ưu tiên'} · {target.title}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {!learned && <Target size={14} className="text-slate-300" />}
                    <button
                      onClick={() => setExpandedSkill(expanded ? null : row.skill)}
                      className="btn-ghost p-1.5"
                      title="Xem lộ trình học"
                      aria-label={`Xem lộ trình học: ${row.skill}`}
                    >
                      {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  </div>
                </div>

                {expanded && (
                  <div className="px-4 pb-4 pt-0 border-t border-white/60">
                    <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2 mt-3">
                      Lộ trình học gợi ý
                    </div>
                    <ol className="space-y-2">
                      {steps.map((step, i) => (
                        <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                          <span className="shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center mt-0.5">
                            {i + 1}
                          </span>
                          {step}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {displayed.length === 0 && (
          <div className="card p-10 text-center text-slate-400 text-sm">
            {total === 0
              ? 'Hồ sơ của bạn đã đáp ứng đầy đủ kỹ năng của công việc này.'
              : 'Không có kỹ năng nào trong nhóm ưu tiên này.'}
          </div>
        )}
      </div>
    </div>
  );
}
