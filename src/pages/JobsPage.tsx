import { useState, useMemo } from 'react';
import { Search, X, SlidersHorizontal } from 'lucide-react';
import type { UseAppState } from '../hooks/useAppState';
import type { FilterState } from '../types';
import { sampleJobs } from '../data/jobs';
import { filterJobs, getAllMatchScores } from '../utils';
import JobCard from '../components/jobs/JobCard';
import JobDetailModal from '../components/jobs/JobDetailModal';
import LoadingBlock from '../components/ui/LoadingBlock';
import { useSimulatedLoading } from '../hooks/useSimulatedLoading';
import type { Job } from '../types';

interface JobsPageProps {
  appState: UseAppState;
}

const locations = ['Tất cả', 'Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Remote'];
const workTypes = ['Toàn thời gian', 'Bán thời gian', 'Thực tập', 'Remote'];
const experienceLevels = ['Chưa có kinh nghiệm', 'Dưới 1 năm', '1-2 năm', '2-3 năm', '3+ năm'];
const categories = [
  'Frontend Development',
  'Backend Development',
  'Data Science & Analytics',
  'Business Analysis',
  'QA & Testing',
  'UI/UX Design',
  'IT Support',
  'Digital Marketing',
  'Software Engineering',
  'Business Operations',
];

const defaultFilters: FilterState = {
  query: '',
  location: 'Tất cả',
  workType: '',
  experienceLevel: '',
  category: '',
  sortBy: 'relevance',
};

export default function JobsPage({ appState }: JobsPageProps) {
  const { studentProfile, isJobSaved, saveJob, unsaveJob, applyToJob, hasApplied } = appState;
  const [filters, setFilters] = useState<FilterState>(defaultFilters);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const matchScores = useMemo(() => getAllMatchScores(studentProfile), [studentProfile]);

  const filteredJobs = useMemo(
    () => filterJobs(sampleJobs, filters, matchScores),
    [filters, matchScores]
  );

  // Giả lập thời gian lọc ngắn sau mỗi lần thay đổi bộ lọc
  const loading = useSimulatedLoading(filters, 250);

  const hasActiveFilters =
    filters.query !== '' ||
    (filters.location !== '' && filters.location !== 'Tất cả') ||
    filters.workType !== '' ||
    filters.experienceLevel !== '' ||
    filters.category !== '';

  const clearFilters = () => setFilters(defaultFilters);

  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const toggleSave = (jobId: string) => {
    if (isJobSaved(jobId)) unsaveJob(jobId);
    else saveJob(jobId);
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Tìm kiếm Việc làm</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Tìm việc phù hợp với kỹ năng của bạn. Điểm phù hợp được tính từ hồ sơ.
        </p>
      </div>

      {/* Search bar */}
      <div className="flex flex-wrap gap-3">
        <div className="relative w-full md:flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Tên công việc, công ty hoặc kỹ năng..."
            className="input-field pl-9"
            value={filters.query}
            onChange={(e) => updateFilter('query', e.target.value)}
          />
          {filters.query && (
            <button
              onClick={() => updateFilter('query', '')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X size={14} />
            </button>
          )}
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`btn-secondary gap-2 ${showFilters ? 'border-blue-300 text-blue-600 bg-blue-50' : ''}`}
        >
          <SlidersHorizontal size={16} />
          Bộ lọc
          {hasActiveFilters && (
            <span className="w-2 h-2 bg-blue-500 rounded-full" />
          )}
        </button>
        <div className="flex items-center gap-2">
          <select
            className="select-field w-auto pr-8"
            value={filters.sortBy}
            onChange={(e) => updateFilter('sortBy', e.target.value as FilterState['sortBy'])}
          >
            <option value="relevance">Phù hợp nhất</option>
            <option value="newest">Mới nhất</option>
          </select>
        </div>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div className="card p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5">Địa điểm</label>
            <select
              className="select-field"
              value={filters.location}
              onChange={(e) => updateFilter('location', e.target.value)}
            >
              {locations.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5">Hình thức</label>
            <select
              className="select-field"
              value={filters.workType}
              onChange={(e) => updateFilter('workType', e.target.value as FilterState['workType'])}
            >
              <option value="">Tất cả</option>
              {workTypes.map((w) => <option key={w} value={w}>{w}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5">Kinh nghiệm</label>
            <select
              className="select-field"
              value={filters.experienceLevel}
              onChange={(e) => updateFilter('experienceLevel', e.target.value as FilterState['experienceLevel'])}
            >
              <option value="">Tất cả</option>
              {experienceLevels.map((e) => <option key={e} value={e}>{e}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5">Lĩnh vực</label>
            <select
              className="select-field"
              value={filters.category}
              onChange={(e) => updateFilter('category', e.target.value as FilterState['category'])}
            >
              <option value="">Tất cả</option>
              {categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          {hasActiveFilters && (
            <div className="col-span-full">
              <button onClick={clearFilters} className="btn-danger text-xs py-1.5">
                <X size={14} />
                Xóa tất cả bộ lọc
              </button>
            </div>
          )}
        </div>
      )}

      {/* Results count */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-500">
          Tìm thấy <span className="font-semibold text-slate-800">{filteredJobs.length}</span> kết quả
        </div>
      </div>

      {/* Job list */}
      {loading ? (
        <LoadingBlock rows={4} message="Đang lọc công việc..." />
      ) : filteredJobs.length === 0 ? (
        <div className="card p-12 text-center">
          <Search size={40} className="mx-auto text-slate-300 mb-3" />
          <h3 className="font-semibold text-slate-600 mb-1">Không tìm thấy kết quả</h3>
          <p className="text-sm text-slate-400 mb-4">
            Thử thay đổi từ khóa hoặc bỏ bớt bộ lọc để xem thêm kết quả.
          </p>
          <button onClick={clearFilters} className="btn-secondary text-sm">
            Xóa bộ lọc
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              matchResult={matchScores.get(job.id)!}
              isSaved={isJobSaved(job.id)}
              onSave={() => toggleSave(job.id)}
              onViewDetail={() => setSelectedJob(job)}
            />
          ))}
        </div>
      )}

      {/* Job detail modal */}
      {selectedJob && (
        <JobDetailModal
          job={selectedJob}
          matchResult={matchScores.get(selectedJob.id)!}
          isSaved={isJobSaved(selectedJob.id)}
          hasApplied={hasApplied(selectedJob.id)}
          onSave={() => toggleSave(selectedJob.id)}
          onApply={() => applyToJob(selectedJob.id)}
          onClose={() => setSelectedJob(null)}
        />
      )}
    </div>
  );
}
