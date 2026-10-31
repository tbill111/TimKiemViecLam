import { api } from './client';
import type {
  ApplicationDTO, AuthResponse, BiFunnel, BiSalary, BiSkillRow, BiSummary, GuestToken, JobDTO, JobInPayload, JobListResponse, MatchDTO,
  ModelId, ProfileDTO, RankedCandidateDTO, ResumeUploadResponse, SkillGapResponse, UserDTO, UploadedSkill,
} from './dto';

export const authApi = {
  login: (email: string, password: string) => api.post<AuthResponse>('/auth/login', { email, password }).then((r) => r.data),
  register: (body: { email: string; password: string; role: 'candidate' | 'recruiter'; full_name: string; company_name?: string }) =>
    api.post<AuthResponse>('/auth/register', body).then((r) => r.data),
  me: () => api.get<UserDTO>('/auth/me').then((r) => r.data),
};

export const jobsApi = {
  list: (params: Record<string, unknown> = {}) => api.get<JobListResponse>('/jobs', { params: { page_size: 200, ...params } }).then((r) => r.data),
  get: (id: string | number) => api.get<JobDTO>(`/jobs/${id}`).then((r) => r.data),
  create: (body: JobInPayload) => api.post<JobDTO>('/jobs', body).then((r) => r.data),
  update: (id: string | number, body: JobInPayload) => api.put<JobDTO>(`/jobs/${id}`, body).then((r) => r.data),
  close: (id: string | number) => api.delete(`/jobs/${id}`).then(() => undefined),
  locations: () => api.get<{ items: { id: number; name: string }[] }>('/locations').then((r) => r.data.items),
  skills: () => api.get<{ items: { id: number; name: string; category: string }[] }>('/skills').then((r) => r.data.items),
};

export const profileApi = {
  get: () => api.get<ProfileDTO>('/candidates/me').then((r) => r.data),
  put: (patch: Record<string, unknown>) => api.put<ProfileDTO>('/candidates/me', patch).then((r) => r.data),
  confirmSkills: (skills: string[]) => api.put<{ skills: string[]; unresolved: string[] }>('/candidates/me/skills', { skills }).then((r) => r.data),
  remove: () => api.delete('/candidates/me').then(() => undefined),
};

export const resumeApi = {
  upload: (file: File, consent: boolean) => {
    const form = new FormData();
    form.append('file', file);
    form.append('consent', String(consent));
    return api.post<ResumeUploadResponse>('/resumes/upload', form).then((r) => r.data);
  },
};

export const aiApi = {
  match: (jobId: string | number, model: ModelId, candidateId?: number) =>
    api.post<MatchDTO>('/ai/match', { job_id: Number(jobId), model, candidate_id: candidateId }).then((r) => r.data),
  matches: (model?: ModelId) =>
    api.get<{ items: { job_id: number; match: MatchDTO }[] }>('/candidates/me/matches', { params: { model } }).then((r) => r.data.items),
  recommendations: (top = 10, model?: ModelId) =>
    api.get<{ items: { job_id: number; match: MatchDTO }[] }>('/candidates/me/recommendations', { params: { top, model } }).then((r) => r.data.items),
  skillGap: (jobId: string | number) => api.get<SkillGapResponse>('/candidates/me/skill-gap', { params: { job_id: Number(jobId) } }).then((r) => r.data),
  extractSkills: (text: string) => api.post<{ skills: UploadedSkill[] }>('/ai/extract-skills', { text }).then((r) => r.data.skills),
  ranked: (jobId: string | number, top = 100, model?: ModelId) =>
    api.get<{ job_id: number; items: RankedCandidateDTO[] }>(`/jobs/${jobId}/ranked-candidates`, { params: { top, model } }).then((r) => r.data.items),
};

export const applicationApi = {
  apply: (jobId: string | number, resumeId?: number) => api.post<ApplicationDTO>('/applications', { job_id: Number(jobId), resume_id: resumeId }).then((r) => r.data),
  mine: () => api.get<{ items: ApplicationDTO[] }>('/applications/me').then((r) => r.data.items),
  setStatus: (id: string | number, status: string, note = '') => api.patch<ApplicationDTO>(`/applications/${id}/status`, { status, note }).then((r) => r.data),
};

export const savedApi = {
  list: () => api.get<{ items: { job_id: number; saved_at: string }[] }>('/saved-jobs').then((r) => r.data.items),
  save: (jobId: string | number) => api.post(`/saved-jobs/${jobId}`).then(() => undefined),
  remove: (jobId: string | number) => api.delete(`/saved-jobs/${jobId}`).then(() => undefined),
};

export const biApi = {
  summary: () => api.get<BiSummary>('/bi/summary').then((r) => r.data),
  skills: () => api.get<{ items: BiSkillRow[] }>('/bi/skills').then((r) => r.data.items),
  salary: () => api.get<BiSalary>('/bi/salary').then((r) => r.data),
  funnel: () => api.get<BiFunnel>('/bi/funnel').then((r) => r.data),
  guestToken: () => api.get<GuestToken>('/bi/guest-token').then((r) => r.data),
};

export interface AdminSkill {
  id: number;
  name: string;
  category: string;
  learning_steps: string[];
}

export const adminApi = {
  skills: () => api.get<{ items: AdminSkill[] }>('/admin/skills').then((r) => r.data.items),
  addSkill: (body: { name: string; category: string; learning_steps?: string[] }) => api.post<AdminSkill>('/admin/skills', body).then((r) => r.data),
  updateSkill: (id: number, body: { category?: string; learning_steps?: string[] }) => api.put<AdminSkill>(`/admin/skills/${id}`, body).then((r) => r.data),
  aliases: () => api.get<{ items: { alias: string; skill_name: string }[] }>('/admin/skill-aliases').then((r) => r.data.items),
  addAlias: (alias: string, skill_name: string) => api.post('/admin/skill-aliases', { alias, skill_name }).then((r) => r.data),
  deleteAlias: (alias: string) => api.delete(`/admin/skill-aliases/${encodeURIComponent(alias)}`).then(() => undefined),
};
