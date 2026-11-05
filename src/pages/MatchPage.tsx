import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, XCircle, Info } from 'lucide-react';
import type { UseAppState } from '../hooks/useAppState';
import type { SkillMatchResult } from '../types';
import { useJobs } from '../context/JobsContext';
import { OFFLINE } from '../config';
import { aiApi } from '../api/endpoints';
import { toMatch } from '../api/adapters';
import { errorMessage } from '../api/client';
import type { ModelId } from '../api/dto';
import ScoreBreakdown from '../components/jobs/ScoreBreakdown';
import ErrorBlock from '../components/ui/ErrorBlock';
import EmptyBlock from '../components/ui/EmptyBlock';
import LoadingBlock from '../components/ui/LoadingBlock';

interface MatchPageProps {
  appState: UseAppState;
}

const MODELS: { id: ModelId; label: string; hint: string }[] = [
  { id: 'm0', label: 'M0 – Quy tắc 60/25/15', hint: 'Baseline: 60% kỹ năng bắt buộc + 25% ưu tiên + 15% mong muốn.' },
  { id: 'm1', label: 'M1 – TF-IDF', hint: 'Độ tương tự từ vựng giữa CV và mô tả công việc.' },
  { id: 'm2', label: 'M2 – Embedding', hint: 'Độ gần về ngữ nghĩa (mô hình đa ngôn ngữ).' },
  { id: 'm3', label: 'M3 – Hybrid', hint: 'Kết hợp 6 đặc trưng với trọng số cố định và luật chặn ≤ 50 khi thiếu hơn nửa kỹ năng bắt buộc.' },
  { id: 'm4', label: 'M4 – Logistic Regression', hint: 'Trọng số học từ dữ liệu gán nhãn (cần huấn luyện trước).' },
  { id: 'm5', label: 'M5 – Random Forest', hint: 'Rừng ngẫu nhiên học từ dữ liệu gán nhãn trên 6 đặc trưng; bắt được tương tác giữa các đặc trưng (cần huấn luyện trước).' },
  { id: 'm6', label: 'M6 – Gradient Boosting', hint: 'Các cây nông nối tiếp nhau học từ dữ liệu gán nhãn trên 6 đặc trưng (cần huấn luyện trước).' },
];

const getBarColor = (score: number) => {
  if (score >= 80) return 'bg-emerald-500';
  if (score >= 60) return 'bg-blue-500';
  if (score >= 40) return 'bg-amber-500';
  return 'bg-slate-400';
};

const pct = (v: number | null | undefined) => (v == null ? '—' : `${v}%`);

export default function MatchPage({ appState }: MatchPageProps) {
  const { jobs, getMatch, loading: jobsLoading, error: jobsError, reload } = useJobs();
  void appState;
  // Model chọn ở trang này chỉ dùng để chấm cặp đang xem; danh sách bên trái luôn dùng model mặc định (M3)
  const [model, setModel] = useState<ModelId>('m3');
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [remote, setRemote] = useState<SkillMatchResult | null>(null);
  const [remoteError, setRemoteError] = useState<string | null>(null);
  const [remoteLoading, setRemoteLoading] = useState(false);

  const selectedJob = useMemo(() => jobs.find((j) => j.id === selectedJobId) ?? jobs[0], [jobs, selectedJobId]);

  // Online: chấm riêng cặp (hồ sơ, tin đang chọn) bằng model đã chọn để xem 6 thành phần và câu giải thích
  useEffect(() => {
    if (OFFLINE || !selectedJob) return;
    let cancelled = false;
    setRemoteLoading(true);
    setRemoteError(null);
    aiApi
      .match(selectedJob.id, model)
      .then((m) => !cancelled && setRemote(toMatch(m, selectedJob.id)))
      .catch((e) => {
        if (cancelled) return;
        setRemote(null);
        setRemoteError(errorMessage(e));
      })
      .finally(() => !cancelled && setRemoteLoading(false));
    return () => {
      cancelled = true;
    };
  }, [selectedJob, model]);

  if (!OFFLINE && jobsError) return <ErrorBlock message={jobsError} onRetry={reload} />;
  if (!OFFLINE && jobsLoading) return <LoadingBlock rows={3} message="Đang tải tin tuyển dụng..." />;
  if (!selectedJob) return <EmptyBlock title="Chưa có tin tuyển dụng" hint="Hãy quay lại sau khi có tin được đăng." />;

  const matchResult: SkillMatchResult = OFFLINE ? getMatch(selectedJob) : remote ?? getMatch(selectedJob);
  const modelInfo = MODELS.find((m) => m.id === model);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Phân tích Mức độ Phù hợp CV–JD</h1>
          <p className="text-slate-500 text-sm mt-0.5">So sánh kỹ năng trong hồ sơ với yêu cầu của từng vị trí tuyển dụng.</p>
        </div>
        {!OFFLINE && (
          <div>
            <label htmlFor="match-model" className="block text-xs font-medium text-slate-500 mb-1">Mô hình chấm điểm</label>
            <select id="match-model" className="select-field" value={model} onChange={(e) => setModel(e.target.value as ModelId)}>
              {MODELS.map((m) => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-100 rounded-xl text-sm text-amber-700">
        <Info size={16} className="shrink-0 mt-0.5" />
        <span>
          {OFFLINE ? (
            <>
              <strong>Mô phỏng ghép nối đa tiêu chí.</strong> Điểm phù hợp = 60% kỹ năng bắt buộc + 25% kỹ năng ưu tiên + 15% mong muốn
              (địa điểm, hình thức). Tính bằng quy tắc, không phải kết quả của mô hình AI thật.
            </>
          ) : (
            <>
              <strong>{modelInfo?.label}.</strong> {modelInfo?.hint} Điểm là gợi ý hỗ trợ quyết định, không thay thế đánh giá của nhà tuyển dụng;
              mô hình không dùng tên, giới tính hay tuổi.
            </>
          )}
        </span>
      </div>

      {!OFFLINE && matchResult.modelVersion?.includes('ai-labels') && (
        <div role="note" className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-100 rounded-xl text-sm text-amber-800">
          <Info size={16} className="shrink-0 mt-0.5" />
          <span>Mô hình <strong>{matchResult.modelVersion}</strong> được huấn luyện trên nhãn do <strong>agent AI</strong> gán (300 cặp, 30 ứng viên), không phải nhãn của nhà tuyển dụng. Điểm chỉ để tham khảo.</span>
        </div>
      )}

      {remoteError && <ErrorBlock message={remoteError} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left – Select job */}
        <div className="card p-5 space-y-3">
          <h2 className="section-title text-sm">Chọn vị trí để phân tích</h2>
          <div className="space-y-2 max-h-[480px] overflow-y-auto scrollbar-thin pr-1">
            {jobs.map((job) => {
              const result = getMatch(job);
              const isSelected = job.id === selectedJob.id;
              return (
                <button
                  key={job.id}
                  onClick={() => setSelectedJobId(job.id)}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
                    isSelected ? 'border-blue-300 bg-blue-50' : 'border-slate-100 hover:border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="font-medium text-sm text-slate-800 truncate">{job.title}</div>
                  <div className="text-xs text-slate-400 mt-0.5">{job.company}</div>
                  <div className="flex items-center gap-2 mt-1.5">
                    <div className="flex-1 progress-bar h-1.5">
                      <div className={`progress-fill ${getBarColor(result.matchScore)}`} style={{ width: `${result.matchScore}%` }} />
                    </div>
                    <span className="text-xs font-bold text-slate-600 shrink-0">{result.matchScore}%</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right – Analysis */}
        <div className={`lg:col-span-2 space-y-4 ${remoteLoading ? 'opacity-60' : ''}`}>
          <div className="card p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">{selectedJob.title}</h2>
                <div className="text-sm text-slate-500 mt-0.5">{selectedJob.company} · {selectedJob.location}</div>
              </div>
              <div className="text-center">
                <div
                  className={`text-4xl font-extrabold ${
                    matchResult.matchScore >= 80 ? 'text-emerald-600'
                    : matchResult.matchScore >= 60 ? 'text-blue-600'
                    : matchResult.matchScore >= 40 ? 'text-amber-600'
                    : 'text-slate-500'
                  }`}
                >
                  {matchResult.matchScore}%
                </div>
                <div className="text-xs text-slate-400 mt-0.5">Điểm phù hợp</div>
              </div>
            </div>

            <div className="mt-4 progress-bar h-3">
              <div className={`progress-fill ${getBarColor(matchResult.matchScore)}`} style={{ width: `${matchResult.matchScore}%` }} />
            </div>
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>0%</span>
              <span>{matchResult.matchedSkills.length}/{matchResult.totalRequired} kỹ năng bắt buộc đáp ứng</span>
              <span>100%</span>
            </div>
            {matchResult.explanation && (
              <p className="mt-4 text-sm text-slate-600 bg-slate-50 border border-slate-100 rounded-lg p-3">{matchResult.explanation}</p>
            )}
          </div>

          <div className="card p-5">
            <h3 className="font-semibold text-sm text-slate-800 mb-3">Điểm được tính như thế nào</h3>
            <ScoreBreakdown result={matchResult} />
            {!OFFLINE && matchResult.semanticScore !== undefined && (
              <dl className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm" aria-label="Sáu thành phần điểm">
                {[
                  ['Kỹ năng bắt buộc', matchResult.requiredScore],
                  ['Kỹ năng ưu tiên', matchResult.preferredScore],
                  ['Ngữ nghĩa CV–JD', matchResult.semanticScore],
                  ['Kinh nghiệm', matchResult.expScore],
                  ['Học vấn', matchResult.eduScore],
                  ['Mong muốn', matchResult.preferenceScore],
                ].map(([label, value]) => (
                  <div key={label as string} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <dt className="text-xs text-slate-400">{label}</dt>
                    <dd className="font-bold text-slate-800">{pct(value as number | null)}</dd>
                  </div>
                ))}
              </dl>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 size={16} className="text-emerald-500" />
                <h3 className="font-semibold text-sm text-slate-800">Kỹ năng đã có ({matchResult.matchedSkills.length})</h3>
              </div>
              {matchResult.matchedSkills.length === 0 ? (
                <p className="text-sm text-slate-400">Chưa đáp ứng kỹ năng nào.</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {matchResult.matchedSkills.map((s) => (
                    <span key={s} className="skill-tag-matched"><CheckCircle2 size={11} />{s}</span>
                  ))}
                </div>
              )}
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <XCircle size={16} className="text-red-500" />
                <h3 className="font-semibold text-sm text-slate-800">Kỹ năng còn thiếu ({matchResult.missingSkills.length})</h3>
              </div>
              {matchResult.missingSkills.length === 0 ? (
                <p className="text-sm text-emerald-600 font-medium">Bạn đáp ứng đầy đủ yêu cầu!</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {matchResult.missingSkills.map((s) => (
                    <span key={s} className="skill-tag-missing"><XCircle size={11} />{s}</span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {selectedJob.preferredSkills.length > 0 && (
            <div className="card p-5">
              <h3 className="font-semibold text-sm text-slate-800 mb-3">Kỹ năng ưu tiên thêm</h3>
              <div className="flex flex-wrap gap-1.5">
                {selectedJob.preferredSkills.map((s) =>
                  matchResult.matchedPreferred.includes(s) ? (
                    <span key={s} className="skill-tag-matched"><CheckCircle2 size={11} />{s}</span>
                  ) : (
                    <span key={s} className="badge-gray">{s}</span>
                  )
                )}
              </div>
              <p className="text-xs text-slate-400 mt-2">Kỹ năng ưu tiên không bắt buộc nhưng giúp hồ sơ của bạn nổi bật hơn.</p>
            </div>
          )}

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
                  <li className="text-xs text-blue-500 italic">Và {matchResult.missingSkills.length - 3} kỹ năng khác...</li>
                )}
              </ul>
            </div>
          )}

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
