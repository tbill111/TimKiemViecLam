import type { Application, ApplicationStatus, ExperienceLevel, Job, JobCategory, SkillMatchResult, StudentProfile, WorkType } from '../types';
import type { ApiStatus, ApplicationDTO, JobDTO, MatchDTO, ProfileDTO } from './dto';

/** 6 trạng thái: nhãn tiếng Việt của frontend ↔ mã của backend. */
export const STATUS_LABEL: Record<ApiStatus, ApplicationStatus> = {
  applied: 'Đã ứng tuyển',
  screening: 'Đang xem xét',
  interview: 'Phỏng vấn',
  offer: 'Đề nghị',
  hired: 'Đã tuyển',
  rejected: 'Từ chối',
};

export const STATUS_CODE: Record<ApplicationStatus, ApiStatus> = {
  'Đã ứng tuyển': 'applied',
  'Đang xem xét': 'screening',
  'Phỏng vấn': 'interview',
  'Đề nghị': 'offer',
  'Đã tuyển': 'hired',
  'Từ chối': 'rejected',
};

/** Luồng chuyển hợp lệ (backend trả 409 nếu sai): tiến một bước hoặc từ chối khi chưa kết thúc. */
export const NEXT_STATUS: Partial<Record<ApiStatus, ApiStatus>> = {
  applied: 'screening',
  screening: 'interview',
  interview: 'offer',
  offer: 'hired',
};

export const FINAL_STATUSES: ApiStatus[] = ['hired', 'rejected'];

export function allowedNext(status: ApiStatus): ApiStatus[] {
  if (FINAL_STATUSES.includes(status)) return [];
  const next = NEXT_STATUS[status];
  return next ? [next, 'rejected'] : ['rejected'];
}

export function workTypeOf(d: Pick<JobDTO, 'job_type' | 'work_mode'>): WorkType {
  if (d.work_mode === 'remote') return 'Remote';
  return d.job_type === 'internship' ? 'Thực tập' : d.job_type === 'part_time' ? 'Bán thời gian' : 'Toàn thời gian';
}

/** Ngược lại với workTypeOf, dùng khi đăng tin. */
export function jobTypeFields(label: WorkType): { job_type: string; work_mode: string } {
  switch (label) {
    case 'Remote': return { job_type: 'full_time', work_mode: 'remote' };
    case 'Thực tập': return { job_type: 'internship', work_mode: 'onsite' };
    case 'Bán thời gian': return { job_type: 'part_time', work_mode: 'onsite' };
    default: return { job_type: 'full_time', work_mode: 'onsite' };
  }
}

export function experienceOf(years: number): ExperienceLevel {
  if (years <= 0) return 'Chưa có kinh nghiệm';
  if (years < 1) return 'Dưới 1 năm';
  if (years < 2) return '1-2 năm';
  if (years < 3) return '2-3 năm';
  return '3+ năm';
}

const million = (v: number) => Math.round(v * 1_000_000).toLocaleString('en-US');

export function formatSalary(min: number | null, max: number | null): string {
  if (min == null || max == null) return 'Thỏa thuận';
  return `${million(min)} – ${million(max)} VNĐ/tháng`;
}

/** Backend trả giờ UTC không kèm múi giờ; thêm 'Z' để trình duyệt hiểu đúng. */
export const asUtc = (iso: string | null): string => (iso ? (/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`) : new Date().toISOString());

export function toJob(d: JobDTO): Job {
  return {
    id: String(d.id),
    title: d.title,
    company: d.company.name,
    location: d.location,
    workType: workTypeOf(d),
    experienceLevel: experienceOf(d.min_years_exp),
    salary: formatSalary(d.salary_min, d.salary_max),
    description: d.description,
    responsibilities: d.responsibilities,
    requiredSkills: d.required_skills,
    preferredSkills: d.preferred_skills,
    postedAt: asUtc(d.posted_at),
    category: d.category as JobCategory,
    companySize: d.company.size_range,
    companyIndustry: d.company.industry,
    salaryMin: d.salary_min,
    salaryMax: d.salary_max,
    status: d.status,
  };
}

/** MatchDTO → SkillMatchResult (ánh xạ ở docs/00_KE_HOACH_KY_THUAT_TH3.md mục 3.4). */
export function toMatch(m: MatchDTO, jobId: string): SkillMatchResult {
  const c = m.components;
  return {
    jobId,
    matchScore: m.total_score,
    matchedSkills: m.matched_required,
    missingSkills: m.missing_required,
    totalRequired: m.matched_required.length + m.missing_required.length,
    matchedPreferred: m.matched_preferred,
    missingPreferred: m.missing_preferred,
    requiredScore: c.skill_req ?? 0,
    preferredScore: c.skill_pref ?? 0,
    preferenceScore: c.pref ?? 0,
    locationMatch: m.location_match,
    workTypeMatch: m.work_type_match,
    semanticScore: c.semantic,
    expScore: c.exp,
    eduScore: c.edu,
    explanation: m.explanation,
    model: m.model,
    modelVersion: m.model_version,
  };
}

export function toApplication(d: ApplicationDTO): Application {
  return { id: String(d.id), jobId: String(d.job_id), appliedAt: asUtc(d.applied_at), status: STATUS_LABEL[d.status] };
}

export function toProfile(d: ProfileDTO): StudentProfile {
  return {
    fullName: d.fullName,
    university: d.university,
    major: d.major,
    year: d.year,
    email: d.email,
    phone: d.phone,
    githubUrl: d.githubUrl,
    linkedinUrl: d.linkedinUrl,
    careerGoal: d.careerGoal,
    skills: d.skills,
    preferredLocations: d.preferredLocations,
    preferredWorkTypes: d.preferredWorkTypes as WorkType[],
    languages: d.languages,
    projects: d.projects as StudentProfile['projects'],
    experience: d.experience as StudentProfile['experience'],
    certificates: d.certificates as StudentProfile['certificates'],
    profileCompletion: d.profileCompletion,
  };
}

/** Phần hồ sơ gửi lên khi lưu (bỏ trường chỉ đọc). */
export function fromProfilePatch(patch: Partial<StudentProfile>): Record<string, unknown> {
  const { profileCompletion: _ignored, email: _email, ...rest } = patch;
  void _ignored;
  void _email;
  return rest;
}
