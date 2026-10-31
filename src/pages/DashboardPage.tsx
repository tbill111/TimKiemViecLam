import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Briefcase,
  Bookmark,
  FileCheck,
  UserCircle,
  ArrowRight,
  TrendingUp,
  Star,
  ChevronRight,
  Lightbulb,
  BarChart2,
} from 'lucide-react';
import type { UseAppState } from '../hooks/useAppState';
import { useSimulatedLoading } from '../hooks/useSimulatedLoading';
import { sampleJobs } from '../data/jobs';
import { skillCategories } from '../data/skillCategories';
import {
  calculateSkillMatch,
  countJobsWithSkill,
  countSuitableJobs,
  getAllMatchScores,
  getSkillCoverage,
  SUITABLE_THRESHOLD,
} from '../utils';
import LoadingBlock from '../components/ui/LoadingBlock';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts';

interface DashboardPageProps {
  appState: UseAppState;
}

const getScoreColor = (score: number) => {
  if (score >= 80) return 'text-emerald-600 bg-emerald-50 border-emerald-100';
  if (score >= 60) return 'text-blue-600 bg-blue-50 border-blue-100';
  if (score >= 40) return 'text-amber-600 bg-amber-50 border-amber-100';
  return 'text-slate-500 bg-slate-50 border-slate-100';
};

export default function DashboardPage({ appState }: DashboardPageProps) {
  const navigate = useNavigate();
  const { studentProfile, savedJobs, applications } = appState;
  const loading = useSimulatedLoading(null, 400);

  const matchScores = useMemo(() => getAllMatchScores(studentProfile), [studentProfile]);

  const topJobs = useMemo(() => {
    return sampleJobs
      .map((job) => ({ job, score: matchScores.get(job.id)?.matchScore ?? 0 }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 4);
  }, [matchScores]);

  const suitableCount = useMemo(() => countSuitableJobs(studentProfile), [studentProfile]);

  const radarData = useMemo(
    () => skillCategories.map((c) => ({ name: c.name, score: getSkillCoverage(studentProfile, c.skills) })),
    [studentProfile]
  );

  // Các con số trong phần gợi ý đều lấy từ dataset mẫu
  const typeScriptStats = countJobsWithSkill('TypeScript');
  const remoteSuitable = sampleJobs.filter(
    (job) => job.workType === 'Remote' && calculateSkillMatch(studentProfile, job).matchScore >= SUITABLE_THRESHOLD
  ).length;

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tổng quan</h1>
        </div>
        <LoadingBlock rows={3} message="Đang tổng hợp dữ liệu phù hợp với hồ sơ..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Xin chào, {studentProfile.fullName.split(' ').slice(-2).join(' ')}!
        </h1>
        <p className="text-slate-500 mt-1 text-sm">
          SmartCareer giúp bạn tìm việc phù hợp theo kỹ năng và phân tích khoảng trống năng lực.
          Tất cả dữ liệu bên dưới là kết quả mô phỏng từ hồ sơ của bạn.
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium uppercase tracking-wide">Việc phù hợp</span>
            <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
              <Briefcase size={15} className="text-blue-600" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900 mt-1">{suitableCount}</div>
          <div className="text-xs text-emerald-600 font-medium">
            Điểm từ {SUITABLE_THRESHOLD}% trên {sampleJobs.length} tin mẫu
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium uppercase tracking-wide">Đã lưu</span>
            <div className="w-8 h-8 bg-amber-50 rounded-lg flex items-center justify-center">
              <Bookmark size={15} className="text-amber-600" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900 mt-1">{savedJobs.length}</div>
          <div className="text-xs text-slate-400">Việc làm yêu thích</div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium uppercase tracking-wide">Ứng tuyển</span>
            <div className="w-8 h-8 bg-emerald-50 rounded-lg flex items-center justify-center">
              <FileCheck size={15} className="text-emerald-600" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900 mt-1">{applications.length}</div>
          <div className="text-xs text-slate-400">Đơn demo đã nộp</div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium uppercase tracking-wide">Hồ sơ</span>
            <div className="w-8 h-8 bg-purple-50 rounded-lg flex items-center justify-center">
              <UserCircle size={15} className="text-purple-600" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900 mt-1">{studentProfile.profileCompletion}%</div>
          <div className="text-xs text-slate-400">Mức hoàn thiện</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top matched jobs */}
        <div className="lg:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="section-title">Việc làm phù hợp nhất</h2>
              <p className="section-subtitle">Dựa trên kỹ năng trong hồ sơ của bạn</p>
            </div>
            <button
              onClick={() => navigate('/jobs')}
              className="btn-ghost text-xs"
            >
              Xem tất cả <ArrowRight size={14} />
            </button>
          </div>
          <div className="space-y-3">
            {topJobs.map(({ job, score }) => (
              <div
                key={job.id}
                className="flex items-center gap-3 p-3 rounded-xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/30 transition-all cursor-pointer"
                onClick={() => navigate('/jobs')}
              >
                <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center shrink-0">
                  <Briefcase size={16} className="text-slate-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-slate-800 text-sm truncate">{job.title}</div>
                  <div className="text-xs text-slate-500">{job.company} · {job.location}</div>
                </div>
                <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold border ${getScoreColor(score)}`}>
                  <Star size={10} />{score}%
                </div>
                <ChevronRight size={14} className="text-slate-300 shrink-0" />
              </div>
            ))}
          </div>
        </div>

        {/* Skills & Radar */}
        <div className="space-y-4">
          {/* Skill overview */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="section-title text-sm">Kỹ năng nổi bật</h2>
              <button onClick={() => navigate('/skill-gap')} className="btn-ghost text-xs p-1" aria-label="Xem Skill Gap">
                <BarChart2 size={14} />
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5 mb-4">
              {studentProfile.skills.map((s) => (
                <span key={s} className="skill-tag">{s}</span>
              ))}
            </div>
            {/* Mini radar */}
            <div className="mt-2 -mx-2">
              <ResponsiveContainer width="100%" height={160}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <Radar
                    name="Kỹ năng"
                    dataKey="score"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.15}
                  />
                  <Tooltip
                    contentStyle={{ fontSize: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                    formatter={(value) => {
                      const v = typeof value === 'number' ? value : 0;
                      return [`${v}%`, 'Đã có'];
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
              <p className="text-xs text-center text-slate-400 italic -mt-1">
                Tỷ lệ kỹ năng đã có trong từng nhóm (tính từ hồ sơ)
              </p>
            </div>
          </div>

          {/* Profile completion */}
          <div className="card p-5">
            <h2 className="section-title text-sm mb-3">Hoàn thiện hồ sơ</h2>
            <div className="progress-bar mb-2">
              <div
                className="progress-fill bg-blue-500"
                style={{ width: `${studentProfile.profileCompletion}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500 mb-3">
              <span>Hiện tại: {studentProfile.profileCompletion}%</span>
              <span>Mục tiêu: 100%</span>
            </div>
            <button
              onClick={() => navigate('/profile')}
              className="btn-secondary w-full text-xs justify-center"
            >
              Cập nhật hồ sơ
            </button>
          </div>
        </div>
      </div>

      {/* Suggestions */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb size={18} className="text-amber-500" />
          <h2 className="section-title">Gợi ý dành riêng cho bạn</h2>
          <span className="badge-yellow text-xs ml-auto">Mô phỏng ghép nối</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl">
            <div className="font-medium text-blue-800 text-sm mb-1.5">Học TypeScript</div>
            <div className="text-xs text-blue-600">
              TypeScript xuất hiện trong {typeScriptStats.anywhere}/{sampleJobs.length} tin mẫu
              ({typeScriptStats.required} tin yêu cầu bắt buộc). Đây là kỹ năng nên ưu tiên để tăng điểm phù hợp.
            </div>
            <button onClick={() => navigate('/skill-gap')} className="mt-2 text-xs text-blue-700 font-semibold hover:underline flex items-center gap-1">
              Xem lộ trình <ArrowRight size={12} />
            </button>
          </div>
          <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl">
            <div className="font-medium text-emerald-800 text-sm mb-1.5">Cập nhật dự án cá nhân</div>
            <div className="text-xs text-emerald-600">
              Hồ sơ có {studentProfile.projects.length} dự án – hãy bổ sung link GitHub để tăng tính thuyết phục khi ứng tuyển.
            </div>
            <button onClick={() => navigate('/profile')} className="mt-2 text-xs text-emerald-700 font-semibold hover:underline flex items-center gap-1">
              Chỉnh sửa hồ sơ <ArrowRight size={12} />
            </button>
          </div>
          <div className="p-4 bg-purple-50 border border-purple-100 rounded-xl">
            <div className="font-medium text-purple-800 text-sm mb-1.5">Thử tìm Remote Jobs</div>
            <div className="text-xs text-purple-600">
              Có {remoteSuitable} vị trí Remote phù hợp với kỹ năng của bạn. Cơ hội tốt để tích lũy kinh nghiệm thực tế.
            </div>
            <button onClick={() => navigate('/jobs')} className="mt-2 text-xs text-purple-700 font-semibold hover:underline flex items-center gap-1">
              Tìm việc ngay <ArrowRight size={12} />
            </button>
          </div>
        </div>
      </div>

      {/* Quick nav */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <button
          onClick={() => navigate('/jobs')}
          className="card p-4 flex items-center gap-3 hover:border-blue-200 hover:bg-blue-50/30 transition-all text-left"
        >
          <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
            <Briefcase size={18} className="text-blue-600" />
          </div>
          <div>
            <div className="font-semibold text-sm text-slate-800">Tìm việc làm</div>
            <div className="text-xs text-slate-400">{suitableCount} việc phù hợp với hồ sơ của bạn</div>
          </div>
          <ArrowRight size={16} className="text-slate-300 ml-auto" />
        </button>
        <button
          onClick={() => navigate('/match')}
          className="card p-4 flex items-center gap-3 hover:border-blue-200 hover:bg-blue-50/30 transition-all text-left"
        >
          <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
            <TrendingUp size={18} className="text-emerald-600" />
          </div>
          <div>
            <div className="font-semibold text-sm text-slate-800">Phân tích CV–JD</div>
            <div className="text-xs text-slate-400">So sánh hồ sơ và yêu cầu</div>
          </div>
          <ArrowRight size={16} className="text-slate-300 ml-auto" />
        </button>
      </div>
    </div>
  );
}
