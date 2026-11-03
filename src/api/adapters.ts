import type { Application, ApplicationStatus, Job, JobCategory, SkillMatchResult, ExperienceLevel, WorkType } from '../types';
import type { ApplicationDto, MatchDto } from './dto';

const statusLabels: Record<string, ApplicationStatus> = {
  applied: 'Đã ứng tuyển',
  screening: 'Đang xem xét',
  interview: 'Phỏng vấn',
  reviewing: 'Đang xem xét',
  interviewing: 'Phỏng vấn',
  offer: 'Đề nghị nhận việc',
  hired: 'Đã nhận việc',
  rejected: 'Đã từ chối',
  withdrawn: 'Đã từ chối',
};

export function adaptStatus(status: string): ApplicationStatus {
  return statusLabels[status] ?? 'Đã ứng tuyển';
}

export function adaptMatch(jobId: string, dto: MatchDto): SkillMatchResult {
  return {
    jobId,
    matchScore: Math.round(dto.total_score),
    matchedSkills: dto.matched_required,
    missingSkills: dto.missing_required,
    totalRequired: dto.matched_required.length + dto.missing_required.length,
    matchedPreferred: dto.matched_preferred,
    missingPreferred: dto.missing_preferred,
    requiredScore: dto.components.skill_req,
    preferredScore: dto.components.skill_pref,
    preferenceScore: dto.components.pref,
    locationMatch: dto.location_match,
    workTypeMatch: dto.work_type_match,
    semanticScore: dto.components.semantic ?? undefined,
    expScore: dto.components.exp ?? undefined,
    eduScore: dto.components.edu ?? undefined,
    explanation: dto.explanation,
    model: dto.model,
    modelVersion: dto.model_version,
  };
}

export function adaptApplication(dto: ApplicationDto): Application {
  return {
    id: dto.id,
    jobId: dto.job_id,
    appliedAt: dto.applied_at,
    status: adaptStatus(dto.status),
    notes: dto.notes,
  };
}

interface BackendJobDto {
  id: string | number;
  title: string;
  company: { name: string; size?: string; industry?: string } | string;
  location: string;
  job_type?: string;
  work_mode?: string;
  min_years_exp?: number | null;
  salary_min?: number | null;
  salary_max?: number | null;
  description?: string;
  responsibilities?: string[];
  required_skills?: string[];
  preferred_skills?: string[];
  category?: string;
  level?: string;
  status?: string;
  posted_at?: string;
}

function adaptWorkType(job: BackendJobDto): WorkType {
  if (job.work_mode === 'remote') return 'Remote';
  if (job.job_type === 'part_time') return 'Bán thời gian';
  if (job.job_type === 'internship') return 'Thực tập';
  return 'Toàn thời gian';
}

function adaptExperience(years: number | null | undefined): ExperienceLevel {
  if (!years || years <= 0) return 'Chưa có kinh nghiệm';
  if (years < 1) return 'Dưới 1 năm';
  if (years < 2) return '1-2 năm';
  if (years < 3) return '2-3 năm';
  return '3+ năm';
}

function adaptSalary(min: number | null | undefined, max: number | null | undefined): string {
  if (min == null && max == null) return 'Thỏa thuận';
  if (min == null) return `Tối đa ${max} triệu VNĐ/tháng`;
  if (max == null) return `Từ ${min} triệu VNĐ/tháng`;
  return `${min} – ${max} triệu VNĐ/tháng`;
}

export function adaptJob(dto: BackendJobDto): Job {
  const company = typeof dto.company === 'string' ? { name: dto.company } : dto.company;
  return {
    id: String(dto.id),
    title: dto.title,
    company: company.name,
    location: dto.location,
    workType: adaptWorkType(dto),
    experienceLevel: adaptExperience(dto.min_years_exp),
    salary: adaptSalary(dto.salary_min, dto.salary_max),
    salaryMin: dto.salary_min ?? undefined,
    salaryMax: dto.salary_max ?? undefined,
    description: dto.description ?? '',
    responsibilities: dto.responsibilities ?? [],
    requiredSkills: dto.required_skills ?? [],
    preferredSkills: dto.preferred_skills ?? [],
    postedAt: dto.posted_at ?? new Date(0).toISOString(),
    category: (dto.category ?? 'Software Engineering') as JobCategory,
    status: dto.status === 'closed' ? 'closed' : 'open',
    level: dto.level,
    minYearsExp: dto.min_years_exp ?? undefined,
    companySize: company.size,
    companyIndustry: company.industry,
  };
}
