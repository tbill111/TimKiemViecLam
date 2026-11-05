// Hình dạng JSON của backend (xem docs/00_KE_HOACH_KY_THUAT_TH3.md mục 3.4).

export type ApiStatus = 'applied' | 'screening' | 'interview' | 'offer' | 'hired' | 'rejected';
export type ModelId = 'm0' | 'm1' | 'm2' | 'm3' | 'm4' | 'm5' | 'm6';
export type Role = 'candidate' | 'recruiter' | 'admin';

export interface UserDTO {
  id: number;
  email: string;
  role: Role;
  full_name: string;
  company_id: number | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: 'bearer';
  user: UserDTO;
}

export interface MatchDTO {
  model: ModelId;
  model_version: string;
  total_score: number;
  components: {
    skill_req: number | null;
    skill_pref: number | null;
    semantic: number | null;
    exp: number | null;
    edu: number | null;
    pref: number | null;
  };
  matched_required: string[];
  missing_required: string[];
  matched_preferred: string[];
  missing_preferred: string[];
  location_match: boolean;
  work_type_match: boolean;
  explanation: string;
}

export interface JobDTO {
  id: number;
  title: string;
  company: { id: number; name: string; size_range: string; industry: string };
  location: string;
  category: string;
  level: string;
  job_type: 'full_time' | 'part_time' | 'internship';
  work_mode: 'onsite' | 'hybrid' | 'remote';
  salary_min: number | null;
  salary_max: number | null;
  min_years_exp: number;
  min_education: number;
  description: string;
  responsibilities: string[];
  required_skills: string[];
  preferred_skills: string[];
  status: 'open' | 'closed';
  posted_at: string | null;
  deadline: string | null;
  match?: MatchDTO;
}

export interface JobListResponse {
  items: JobDTO[];
  total: number;
  page: number;
  page_size: number;
}

export interface HistoryDTO {
  from_status: ApiStatus | null;
  to_status: ApiStatus;
  changed_at: string;
  note: string;
}

export interface ApplicationDTO {
  id: number;
  job_id: number;
  candidate_id: number;
  status: ApiStatus;
  match_score: number | null;
  applied_at: string;
  updated_at: string;
  history: HistoryDTO[];
  job?: { title: string; company_name: string };
  candidate_name?: string;
}

export interface ProfileDTO {
  fullName: string;
  university: string;
  major: string;
  year: string;
  email: string;
  phone: string;
  githubUrl: string;
  linkedinUrl: string;
  careerGoal: string;
  skills: string[];
  preferredLocations: string[];
  preferredWorkTypes: string[];
  languages: string[];
  projects: unknown[];
  experience: unknown[];
  certificates: unknown[];
  profileCompletion: number;
  consent: boolean;
}

export interface UploadedSkill {
  name: string;
  source: 'dict' | 'fuzzy' | 'embedding';
  confidence: number;
}

export interface ResumeUploadResponse {
  resume_id: number;
  skills: UploadedSkill[];
  years_exp: number;
  education_level: number;
  sections_found: string[];
}

export interface SkillGapResponse {
  job_id: number;
  match_score: number;
  missing: { skill: string; required: boolean; jobs_demanding: number; learning_steps: string[] }[];
}

export interface RankedCandidateDTO {
  candidate_id: number;
  full_name: string;
  application_id: number;
  status: ApiStatus;
  applied_at: string;
  match: MatchDTO;
}

export interface BiSummary {
  candidates: number;
  open_jobs: number;
  applications: number;
  hire_rate: number;
}

export interface BiSkillRow {
  skill: string;
  category: string;
  so_ung_vien: number;
  so_tin_yeu_cau: number;
  shortage: number | null;
}

export interface BiSalary {
  items: { month: string; level: string; median_salary: number; n: number }[];
  overall: { month: string; median_salary: number; n: number }[];
}

export interface BiFunnel {
  stages: { stage: string; count: number; conversion_from_prev: number | null }[];
  total_conversion: number | null;
  median_time_to_hire_days: number | null;
  by_score_band: { band: string; applications: number; hired: number; hire_rate: number | null }[];
}

export interface GuestToken {
  token: string;
  dashboard_id: string;
  superset_domain: string;
}

export interface JobInPayload {
  title: string;
  description: string;
  responsibilities: string[];
  category: string;
  level: string;
  job_type: string;
  work_mode: string;
  location: string;
  salary_min: number | null;
  salary_max: number | null;
  min_years_exp: number;
  min_education: number;
  deadline: string | null;
  required_skills: string[];
  preferred_skills: string[];
}
