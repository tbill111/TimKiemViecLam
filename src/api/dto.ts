import type { Job, StudentProfile } from '../types';

export interface MatchDto {
  model: string;
  model_version: string;
  total_score: number;
  components: {
    skill_req: number;
    skill_pref: number;
    semantic: number | null;
    exp: number | null;
    edu: number | null;
    pref: number;
  };
  matched_required: string[];
  missing_required: string[];
  matched_preferred: string[];
  missing_preferred: string[];
  location_match: boolean;
  work_type_match: boolean;
  explanation: string;
}

export interface MatchEnvelopeDto {
  job_id: string;
  match: MatchDto;
}

export interface JobsResponseDto {
  items: Job[];
  total?: number;
}

export interface ApplicationDto {
  id: string;
  job_id: string;
  applied_at: string;
  status: string;
  notes?: string;
}

export interface ProfileDto extends StudentProfile {}

export interface ApiErrorDetail {
  detail?: string | { detail?: string; from?: string; to?: string };
}

export interface SkillGapDto {
  job_id: string;
  match_score: number;
  missing: Array<{ skill: string; required: boolean; jobs_demanding: number; learning_steps: string[] }>;
}
