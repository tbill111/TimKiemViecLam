import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Sparkles, X, ArrowLeftRight } from 'lucide-react';
import { aiApi, jobsApi } from '../api/endpoints';
import { jobTypeFields, workTypeOf } from '../api/adapters';
import { errorMessage } from '../api/client';
import type { JobInPayload } from '../api/dto';
import type { WorkType } from '../types';
import ErrorBlock from '../components/ui/ErrorBlock';
import LoadingBlock from '../components/ui/LoadingBlock';

const CATEGORIES = [
  'Frontend Development', 'Backend Development', 'Data Science & Analytics', 'Business Analysis', 'QA & Testing',
  'UI/UX Design', 'IT Support', 'Digital Marketing', 'Software Engineering', 'Business Operations',
];
const LEVELS: [string, string][] = [['intern', 'Thực tập'], ['fresher', 'Fresher'], ['junior', 'Junior'], ['middle', 'Middle'], ['senior', 'Senior']];
const WORK_TYPES: WorkType[] = ['Thực tập', 'Toàn thời gian', 'Bán thời gian', 'Remote'];
const EDUCATION: [number, string][] = [[0, 'Không yêu cầu'], [1, 'Trung cấp'], [2, 'Cao đẳng'], [3, 'Đại học'], [4, 'Thạc sĩ trở lên']];

interface FormState {
  title: string;
  description: string;
  responsibilities: string;
  category: string;
  level: string;
  workType: WorkType;
  location: string;
  salaryMin: string;
  salaryMax: string;
  minYears: string;
  minEducation: number;
  deadline: string;
}

const empty: FormState = {
  title: '', description: '', responsibilities: '', category: CATEGORIES[0], level: 'fresher', workType: 'Toàn thời gian',
  location: 'Hà Nội', salaryMin: '', salaryMax: '', minYears: '0', minEducation: 3, deadline: '',
};

/** Đăng tin mới hoặc sửa tin; kỹ năng được đánh dấu bắt buộc/ưu tiên và có thể gợi ý từ mô tả bằng tầng AI. */
export default function PostJobPage() {
  const { id } = useParams();
  const editing = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>(empty);
  const [required, setRequired] = useState<string[]>([]);
  const [preferred, setPreferred] = useState<string[]>([]);
  const [catalog, setCatalog] = useState<string[]>([]);
  const [locations, setLocations] = useState<string[]>(['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Remote']);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(editing);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    jobsApi.skills().then((s) => setCatalog(s.map((x) => x.name))).catch(() => undefined);
    jobsApi.locations().then((l) => l.length && setLocations(l.map((x) => x.name))).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!id) return;
    jobsApi
      .get(id)
      .then((j) => {
        setForm({
          title: j.title, description: j.description, responsibilities: j.responsibilities.join('\n'), category: j.category, level: j.level,
          workType: workTypeOf(j), location: j.location, salaryMin: j.salary_min?.toString() ?? '', salaryMax: j.salary_max?.toString() ?? '',
          minYears: String(j.min_years_exp), minEducation: j.min_education, deadline: j.deadline ? j.deadline.slice(0, 10) : '',
        });
        setRequired(j.required_skills);
        setPreferred(j.preferred_skills);
      })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, [id]);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((f) => ({ ...f, [key]: value }));
  const chosen = useMemo(() => new Set([...required, ...preferred]), [required, preferred]);
  const matches = useMemo(
    () => catalog.filter((s) => !chosen.has(s) && s.toLowerCase().includes(query.trim().toLowerCase())).slice(0, 24),
    [catalog, chosen, query]
  );

  const suggest = async () => {
    setError(null);
    setNotice(null);
    const text = `${form.title}\n${form.description}\n${form.responsibilities}`.trim();
    if (text.length < 10) {
      setNotice('Hãy nhập tiêu đề và mô tả công việc trước khi gợi ý kỹ năng.');
      return;
    }
    try {
      const found = (await aiApi.extractSkills(text)).map((s) => s.name).filter((n) => !chosen.has(n));
      setRequired((r) => [...r, ...found]);
      setNotice(found.length ? `Đã thêm ${found.length} kỹ năng vào nhóm "bắt buộc": ${found.join(', ')}. Hãy chuyển sang "ưu tiên" nếu cần.` : 'Không tìm thấy kỹ năng mới trong mô tả.');
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (required.length === 0) {
      setError('Hãy chọn ít nhất một kỹ năng bắt buộc.');
      return;
    }
    const toNum = (v: string) => (v.trim() === '' ? null : Number(v));
    const payload: JobInPayload = {
      title: form.title.trim(),
      description: form.description.trim(),
      responsibilities: form.responsibilities.split('\n').map((x) => x.trim()).filter(Boolean),
      category: form.category,
      level: form.level,
      ...jobTypeFields(form.workType),
      location: form.workType === 'Remote' ? 'Remote' : form.location,
      salary_min: toNum(form.salaryMin),
      salary_max: toNum(form.salaryMax),
      min_years_exp: Number(form.minYears) || 0,
      min_education: form.minEducation,
      deadline: form.deadline ? `${form.deadline}T00:00:00` : null,
      required_skills: required,
      preferred_skills: preferred,
    };
    setBusy(true);
    try {
      if (id) await jobsApi.update(id, payload);
      else await jobsApi.create(payload);
      navigate('/employer/jobs');
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <LoadingBlock rows={3} message="Đang tải tin tuyển dụng..." />;

  const move = (skill: string, from: 'req' | 'pref') => {
    if (from === 'req') {
      setRequired((r) => r.filter((x) => x !== skill));
      setPreferred((p) => [...p, skill]);
    } else {
      setPreferred((p) => p.filter((x) => x !== skill));
      setRequired((r) => [...r, skill]);
    }
  };

  const chip = (skill: string, from: 'req' | 'pref') => (
    <span key={skill} className={`inline-flex items-center gap-1 text-xs pl-2.5 pr-1 py-1 rounded-full border ${from === 'req' ? 'bg-red-50 text-red-700 border-red-100' : 'bg-blue-50 text-blue-700 border-blue-100'}`}>
      {skill}
      <button type="button" onClick={() => move(skill, from)} title={from === 'req' ? 'Chuyển sang ưu tiên' : 'Chuyển sang bắt buộc'} aria-label={`Chuyển nhóm: ${skill}`} className="p-0.5 hover:bg-white/60 rounded-full">
        <ArrowLeftRight size={11} />
      </button>
      <button type="button" onClick={() => (from === 'req' ? setRequired((r) => r.filter((x) => x !== skill)) : setPreferred((p) => p.filter((x) => x !== skill)))} aria-label={`Bỏ: ${skill}`} className="p-0.5 hover:bg-white/60 rounded-full">
        <X size={11} />
      </button>
    </span>
  );

  return (
    <form onSubmit={submit} className="space-y-6 max-w-4xl" aria-label={editing ? 'Sửa tin tuyển dụng' : 'Đăng tin tuyển dụng'}>
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{editing ? 'Sửa tin tuyển dụng' : 'Đăng tin tuyển dụng'}</h1>
        <p className="text-slate-500 text-sm mt-0.5">Kỹ năng bắt buộc và ưu tiên được dùng để tính điểm phù hợp với ứng viên.</p>
      </div>

      {error && <ErrorBlock message={error} />}

      <div className="card p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="md:col-span-2">
          <label htmlFor="job-title" className="block text-xs font-medium text-slate-500 mb-1">Chức danh</label>
          <input id="job-title" required maxLength={255} className="input-field" value={form.title} onChange={(e) => set('title', e.target.value)} />
        </div>
        <div className="md:col-span-2">
          <label htmlFor="job-desc" className="block text-xs font-medium text-slate-500 mb-1">Mô tả công việc</label>
          <textarea id="job-desc" rows={5} className="input-field" value={form.description} onChange={(e) => set('description', e.target.value)} />
        </div>
        <div className="md:col-span-2">
          <label htmlFor="job-resp" className="block text-xs font-medium text-slate-500 mb-1">Nhiệm vụ chính (mỗi dòng một ý)</label>
          <textarea id="job-resp" rows={4} className="input-field" value={form.responsibilities} onChange={(e) => set('responsibilities', e.target.value)} />
        </div>
        <div>
          <label htmlFor="job-cat" className="block text-xs font-medium text-slate-500 mb-1">Nhóm nghề</label>
          <select id="job-cat" className="select-field" value={form.category} onChange={(e) => set('category', e.target.value)}>
            {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="job-level" className="block text-xs font-medium text-slate-500 mb-1">Cấp bậc</label>
          <select id="job-level" className="select-field" value={form.level} onChange={(e) => set('level', e.target.value)}>
            {LEVELS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="job-type" className="block text-xs font-medium text-slate-500 mb-1">Hình thức làm việc</label>
          <select id="job-type" className="select-field" value={form.workType} onChange={(e) => set('workType', e.target.value as WorkType)}>
            {WORK_TYPES.map((w) => <option key={w}>{w}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="job-loc" className="block text-xs font-medium text-slate-500 mb-1">Địa điểm</label>
          <select id="job-loc" className="select-field" disabled={form.workType === 'Remote'} value={form.workType === 'Remote' ? 'Remote' : form.location} onChange={(e) => set('location', e.target.value)}>
            {locations.map((l) => <option key={l}>{l}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="job-smin" className="block text-xs font-medium text-slate-500 mb-1">Lương tối thiểu (triệu VNĐ/tháng)</label>
          <input id="job-smin" type="number" min={0} step="0.5" className="input-field" value={form.salaryMin} onChange={(e) => set('salaryMin', e.target.value)} placeholder="Để trống = thỏa thuận" />
        </div>
        <div>
          <label htmlFor="job-smax" className="block text-xs font-medium text-slate-500 mb-1">Lương tối đa (triệu VNĐ/tháng)</label>
          <input id="job-smax" type="number" min={0} step="0.5" className="input-field" value={form.salaryMax} onChange={(e) => set('salaryMax', e.target.value)} />
        </div>
        <div>
          <label htmlFor="job-years" className="block text-xs font-medium text-slate-500 mb-1">Kinh nghiệm tối thiểu (năm)</label>
          <input id="job-years" type="number" min={0} max={30} step="0.5" className="input-field" value={form.minYears} onChange={(e) => set('minYears', e.target.value)} />
        </div>
        <div>
          <label htmlFor="job-edu" className="block text-xs font-medium text-slate-500 mb-1">Học vấn tối thiểu</label>
          <select id="job-edu" className="select-field" value={form.minEducation} onChange={(e) => set('minEducation', Number(e.target.value))}>
            {EDUCATION.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="job-deadline" className="block text-xs font-medium text-slate-500 mb-1">Hạn nộp hồ sơ</label>
          <input id="job-deadline" type="date" className="input-field" value={form.deadline} onChange={(e) => set('deadline', e.target.value)} />
        </div>
      </div>

      <div className="card p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="section-title text-sm">Kỹ năng yêu cầu</h2>
          <button type="button" onClick={() => void suggest()} className="btn-secondary text-xs py-1.5">
            <Sparkles size={13} />
            Gợi ý kỹ năng từ mô tả
          </button>
        </div>
        {notice && <p role="status" className="text-xs text-blue-700 bg-blue-50 border border-blue-100 rounded-lg p-2.5">{notice}</p>}
        <div>
          <div className="text-xs font-medium text-slate-500 mb-1.5">Bắt buộc ({required.length})</div>
          <div className="flex flex-wrap gap-1.5 min-h-8">{required.map((s) => chip(s, 'req'))}</div>
        </div>
        <div>
          <div className="text-xs font-medium text-slate-500 mb-1.5">Ưu tiên ({preferred.length})</div>
          <div className="flex flex-wrap gap-1.5 min-h-8">{preferred.map((s) => chip(s, 'pref'))}</div>
        </div>
        <div>
          <label htmlFor="skill-search" className="block text-xs font-medium text-slate-500 mb-1">Thêm từ danh mục kỹ năng (nhấn để thêm vào nhóm bắt buộc)</label>
          <input id="skill-search" className="input-field" placeholder="Tìm kỹ năng..." value={query} onChange={(e) => setQuery(e.target.value)} />
          <div className="flex flex-wrap gap-1.5 mt-2">
            {matches.map((s) => (
              <button key={s} type="button" onClick={() => setRequired((r) => [...r, s])} className="text-xs px-2.5 py-1 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-50">
                + {s}
              </button>
            ))}
            {matches.length === 0 && <span className="text-xs text-slate-400">Không có kỹ năng phù hợp trong danh mục.</span>}
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <button type="submit" disabled={busy} className="btn-primary">{busy ? 'Đang lưu...' : editing ? 'Lưu thay đổi' : 'Đăng tin'}</button>
        <button type="button" onClick={() => navigate('/employer/jobs')} className="btn-secondary">Hủy</button>
      </div>
    </form>
  );
}
