import { useState, useMemo } from 'react';
import { CheckCircle2, XCircle, Info } from 'lucide-react';
import type { UseAppState } from '../hooks/useAppState';
import { sampleJobs } from '../data/jobs';
import { calculateSkillMatch } from '../utils';
import ScoreBreakdown from '../components/jobs/ScoreBreakdown';

interface MatchPageProps {
  appState: UseAppState;
}

export default function MatchPage({ appState }: MatchPageProps) {
  const { studentProfile } = appState;
  const [selectedJobId, setSelectedJobId] = useState<string>(sampleJobs[0].id);

  const selectedJob = useMemo(
    () => sampleJobs.find((j) => j.id === selectedJobId) ?? sampleJobs[0],
    [selectedJobId]
  );

  const matchResult = useMemo(
    () => calculateSkillMatch(studentProfile, selectedJob),
    [studentProfile, selectedJob]
  );

  const getBarColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 60) return 'bg-blue-500';
    if (score >= 40) return 'bg-amber-500';
    return 'bg-slate-400';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Phân tích Mức độ Phù hợp CV–JD</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          So sánh kỹ năng trong hồ sơ với yêu cầu của từng vị trí tuyển dụng.
        </p>
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-100 rounded-xl text-sm text-amber-700">
        <Info size={16} className="shrink-0 mt-0.5" />
        <span>
          <strong>Mô phỏng ghép nối đa tiêu chí.</strong> Điểm phù hợp = 60% kỹ năng bắt buộc + 25% kỹ năng ưu tiên
          + 15% mong muốn (địa điểm, hình thức). Tính bằng quy tắc, không phải kết quả của mô hình AI thật.
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left – Select job */}
        <div className="card p-5 space-y-3">
          <h2 className="section-title text-sm">Chọn vị trí để phân tích</h2>
          <div className="space-y-2 max-h-[480px] overflow-y-auto scrollbar-thin pr-1">
            {sampleJobs.map((job) => {
              const result = calculateSkillMatch(studentProfile, job);
              const isSelected = job.id === selectedJobId;
              return (
                <button
                  key={job.id}
                  onClick={() => setSelectedJobId(job.id)}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
                    isSelected
                      ? 'border-blue-300 bg-blue-50'
                      : 'border-slate-100 hover:border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="font-medium text-sm text-slate-800 truncate">{job.title}</div>
                  <div className="text-xs text-slate-400 mt-0.5">{job.company}</div>
                  <div className="flex items-center gap-2 mt-1.5">
                    <div className="flex-1 progress-bar h-1.5">
                      <div
                        className={`progress-fill ${getBarColor(result.matchScore)}`}
                        style={{ width: `${result.matchScore}%` }}
                      />
                    </div>
                    <span className="text-xs font-bold text-slate-600 shrink-0">{result.matchScore}%</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right – Analysis */}
        <div className="lg:col-span-2 space-y-4">
          {/* Score card */}
          <div className="card p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">{selectedJob.title}</h2>
                <div className="text-sm text-slate-500 mt-0.5">{selectedJob.company} · {selectedJob.location}</div>
              </div>
              <div className="text-center">
                <div className={`text-4xl font-extrabold ${
                  matchResult.matchScore >= 80 ? 'text-emerald-600' :
                  matchResult.matchScore >= 60 ? 'text-blue-600' :
                  matchResult.matchScore >= 40 ? 'text-amber-600' : 'text-slate-500'
                }`}>
                  {matchResult.matchScore}%
                </div>
                <div className="text-xs text-slate-400 mt-0.5">Điểm phù hợp</div>
              </div>
            </div>

            <div className="mt-4 progress-bar h-3">
              <div
                className={`progress-fill ${getBarColor(matchResult.matchScore)}`}
                style={{ width: `${matchResult.matchScore}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>0%</span>
              <span>{matchResult.matchedSkills.length}/{matchResult.totalRequired} kỹ năng bắt buộc đáp ứng</span>
              <span>100%</span>
            </div>
          </div>

          {/* Score breakdown */}
          <div className="card p-5">
            <h3 className="font-semibold text-sm text-slate-800 mb-3">Điểm được tính như thế nào</h3>
            <ScoreBreakdown result={matchResult} />
          </div>

          {/* Skills breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Matched */}
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 size={16} className="text-emerald-500" />
                <h3 className="font-semibold text-sm text-slate-800">
                  Kỹ năng đã có ({matchResult.matchedSkills.length})
                </h3>
              </div>
              {matchResult.matchedSkills.length === 0 ? (
                <p className="text-sm text-slate-400">Chưa đáp ứng kỹ năng nào.</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {matchResult.matchedSkills.map((s) => (
                    <span key={s} className="skill-tag-matched">
                      <CheckCircle2 size={11} />
                      {s}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Missing */}
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <XCircle size={16} className="text-red-500" />
                <h3 className="font-semibold text-sm text-slate-800">
                  Kỹ năng còn thiếu ({matchResult.missingSkills.length})
                </h3>
              </div>
              {matchResult.missingSkills.length === 0 ? (
                <p className="text-sm text-emerald-600 font-medium">Bạn đáp ứng đầy đủ yêu cầu!</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {matchResult.missingSkills.map((s) => (
                    <span key={s} className="skill-tag-missing">
                      <XCircle size={11} />
                      {s}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Preferred skills */}
          {selectedJob.preferredSkills.length > 0 && (
            <div className="card p-5">
              <h3 className="font-semibold text-sm text-slate-800 mb-3">Kỹ năng ưu tiên thêm</h3>
              <div className="flex flex-wrap gap-1.5">
                {selectedJob.preferredSkills.map((s) =>
                  matchResult.matchedPreferred.includes(s) ? (
                    <span key={s} className="skill-tag-matched">
                      <CheckCircle2 size={11} />
                      {s}
                    </span>
                  ) : (
                    <span key={s} className="badge-gray">{s}</span>
                  )
                )}
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Kỹ năng ưu tiên không bắt buộc nhưng giúp hồ sơ của bạn nổi bật hơn.
              </p>
            </div>
          )}

          {/* Suggestions */}
          {matchResult.missingSkills.length > 0 && (
            <div className="card p-5 bg-blue-50 border-blue-100">
              <h3 className="font-semibold text-sm text-blue-800 mb-2">Gợi ý cải thiện</h3>
              <ul className="space-y-1.5">
                {matchResult.missingSkills.slice(0, 3).map((s) => (
                  <li key={s} className="flex items-center gap-2 text-sm text-blue-700">
                    <div className="w-1.5 h-1.5 bg-blue-400 rounded-full shrink-0" />
                    Tìm hiểu và thực hành <strong>{s}</strong> để tăng điểm phù hợp
                  </li>
                ))}
                {matchResult.missingSkills.length > 3 && (
                  <li className="text-xs text-blue-500 italic">
                    Và {matchResult.missingSkills.length - 3} kỹ năng khác...
                  </li>
                )}
              </ul>
            </div>
          )}

          {/* All required skills */}
          <div className="card p-5">
            <h3 className="font-semibold text-sm text-slate-800 mb-3">Tất cả kỹ năng yêu cầu</h3>
            <div className="flex flex-wrap gap-1.5">
              {selectedJob.requiredSkills.map((s) => {
                const matched = matchResult.matchedSkills.includes(s);
                return (
                  <span key={s} className={matched ? 'skill-tag-matched' : 'skill-tag-missing'}>
                    {matched ? <CheckCircle2 size={11} /> : <XCircle size={11} />}
                    {s}
                  </span>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
