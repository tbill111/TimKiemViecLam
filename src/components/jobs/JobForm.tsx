import { useState } from 'react';
import type { FormEvent } from 'react';
import type { Job } from '../../types';
import { createJob, updateJob } from '../../api/employer';
import { apiClient, apiErrorMessage, isOfflineDemo } from '../../api/client';

type JobFormValues = {
  title: string;
  description: string;
  category: string;
  location: string;
  job_type: string;
  work_mode: string;
  level: string;
  min_years_exp: string;
  salary_min: string;
  salary_max: string;
  responsibilities: string;
  required_skills: string;
  preferred_skills: string;
};

function initialValues(job?: Job): JobFormValues {
  return {
    title: job?.title ?? '',
    description: job?.description ?? '',
    category: job?.category ?? 'Frontend Development',
    location: job?.location ?? 'Hà Nội',
    job_type: job?.workType === 'Bán thời gian' ? 'part_time' : job?.workType === 'Thực tập' ? 'internship' : 'full_time',
    work_mode: job?.workType === 'Remote' ? 'remote' : 'onsite',
    level: job?.level ?? 'fresher',
    min_years_exp: String(job?.minYearsExp ?? 0),
    salary_min: job?.salaryMin?.toString() ?? '',
    salary_max: job?.salaryMax?.toString() ?? '',
    responsibilities: job?.responsibilities.join('\n') ?? '',
    required_skills: job?.requiredSkills.join(', ') ?? '',
    preferred_skills: job?.preferredSkills.join(', ') ?? '',
  };
}

interface JobFormProps {
  job?: Job;
  onSaved: () => void;
  onCancel: () => void;
}

export default function JobForm({ job, onSaved, onCancel }: JobFormProps) {
  const [form, setForm] = useState<JobFormValues>(() => initialValues(job));
  const [error, setError] = useState('');
  const [suggesting, setSuggesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [suggestedSkills, setSuggestedSkills] = useState<Array<{ name: string; priority: 'required' | 'preferred' }>>([]);
  const set = (key: keyof JobFormValues, value: string) => setForm((old) => ({ ...old, [key]: value }));
  const suggest = async () => {
    if (isOfflineDemo || !form.description) return;
    setSuggesting(true);
    try {
      const response = await apiClient.post<{ skills: Array<{ name: string }> }>('/ai/extract-skills', { text: form.description });
      setSuggestedSkills(response.data.skills.map((skill) => ({ name: skill.name, priority: 'preferred' })));
    } catch (e) {
      setError(apiErrorMessage(e, 'Không gợi ý được kỹ năng.'));
    } finally {
      setSuggesting(false);
    }
  };
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = {
        ...form,
        min_years_exp: Number(form.min_years_exp),
        salary_min: form.salary_min ? Number(form.salary_min) : null,
        salary_max: form.salary_max ? Number(form.salary_max) : null,
        responsibilities: form.responsibilities.split('\n').map((item) => item.trim()).filter(Boolean),
        required_skills: [...form.required_skills.split(',').map((item) => item.trim()).filter(Boolean), ...suggestedSkills.filter((skill) => skill.priority === 'required').map((skill) => skill.name)],
        preferred_skills: [...form.preferred_skills.split(',').map((item) => item.trim()).filter(Boolean), ...suggestedSkills.filter((skill) => skill.priority === 'preferred').map((skill) => skill.name)],
      };
      if (!isOfflineDemo) {
        if (job) await updateJob(job.id, payload);
        else await createJob(payload);
      }
      onSaved();
    } catch (e) {
      setError(apiErrorMessage(e, job ? 'Không lưu được thay đổi.' : 'Không đăng được tin.'));
    } finally {
      setSaving(false);
    }
  };
  return (
    <form onSubmit={submit} className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{job ? 'Sửa tin tuyển dụng' : 'Đăng tin tuyển dụng'}</h1>
      </div>
      <div className="card p-5 space-y-3">
        <input className="input-field" placeholder="Tiêu đề" value={form.title} onChange={(e) => set('title', e.target.value)} required />
        <textarea className="input-field min-h-32" placeholder="Mô tả công việc" value={form.description} onChange={(e) => set('description', e.target.value)} required />
        <div className="grid md:grid-cols-2 gap-3">
          <select className="select-field" value={form.category} onChange={(e) => set('category', e.target.value)}><option>Frontend Development</option><option>Backend Development</option><option>Data Science & Analytics</option><option>Business Analysis</option><option>QA & Testing</option><option>UI/UX Design</option><option>IT Support</option><option>Software Engineering</option></select>
          <select className="select-field" value={form.level} onChange={(e) => set('level', e.target.value)}><option value="intern">Thực tập</option><option value="fresher">Fresher</option><option value="junior">Junior</option><option value="middle">Middle</option><option value="senior">Senior</option></select>
          <select className="select-field" value={form.job_type} onChange={(e) => set('job_type', e.target.value)}><option value="full_time">Toàn thời gian</option><option value="part_time">Bán thời gian</option><option value="internship">Thực tập</option></select>
          <select className="select-field" value={form.work_mode} onChange={(e) => set('work_mode', e.target.value)}><option value="onsite">Tại văn phòng</option><option value="hybrid">Hybrid</option><option value="remote">Remote</option></select>
          <input className="input-field" placeholder="Địa điểm" value={form.location} onChange={(e) => set('location', e.target.value)} />
          <input className="input-field" type="number" placeholder="Số năm kinh nghiệm" value={form.min_years_exp} onChange={(e) => set('min_years_exp', e.target.value)} />
          <input className="input-field" type="number" min="0" step="0.1" placeholder="Lương tối thiểu (triệu VNĐ/tháng)" value={form.salary_min} onChange={(e) => set('salary_min', e.target.value)} />
          <input className="input-field" type="number" min="0" step="0.1" placeholder="Lương tối đa (triệu VNĐ/tháng)" value={form.salary_max} onChange={(e) => set('salary_max', e.target.value)} />
        </div>
        <textarea className="input-field min-h-24" placeholder="Trách nhiệm công việc (mỗi dòng một nội dung)" value={form.responsibilities} onChange={(e) => set('responsibilities', e.target.value)} />
        <button type="button" className="btn-secondary" onClick={() => void suggest()} disabled={suggesting}>{suggesting ? 'Đang gợi ý...' : 'Gợi ý kỹ năng từ mô tả'}</button>
        <div className="grid md:grid-cols-2 gap-3">
          <input className="input-field" placeholder="Kỹ năng bắt buộc" value={form.required_skills} onChange={(e) => set('required_skills', e.target.value)} />
          <input className="input-field" placeholder="Kỹ năng ưu tiên" value={form.preferred_skills} onChange={(e) => set('preferred_skills', e.target.value)} />
        </div>
        {suggestedSkills.length > 0 && <div className="rounded-lg border border-blue-100 bg-blue-50 p-3"><p className="mb-2 text-xs font-semibold text-blue-800">Kỹ năng gợi ý - chọn loại kỹ năng</p><div className="flex flex-wrap gap-2">{suggestedSkills.map((skill) => <label className="flex items-center gap-1 rounded-full bg-white px-2 py-1 text-xs" key={skill.name}><span>{skill.name}</span><select className="rounded border-slate-200 text-xs" value={skill.priority} onChange={(e) => setSuggestedSkills((items) => items.map((item) => item.name === skill.name ? { ...item, priority: e.target.value as 'required' | 'preferred' } : item))}><option value="required">Bắt buộc</option><option value="preferred">Ưu tiên</option></select></label>)}</div></div>}
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        <div className="flex gap-2"><button className="btn-primary" type="submit" disabled={saving}>{saving ? 'Đang lưu...' : job ? 'Lưu thay đổi' : 'Đăng tin'}</button><button className="btn-secondary" type="button" onClick={onCancel}>Hủy</button></div>
      </div>
    </form>
  );
}
