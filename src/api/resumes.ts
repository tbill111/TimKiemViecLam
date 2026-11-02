import { apiClient } from './client';

export interface ExtractedSkill {
  name: string;
  source: 'dict' | 'fuzzy' | 'embedding';
  confidence: number;
}

export interface ResumeUploadResult {
  resume_id: string;
  skills: ExtractedSkill[];
  years_exp: number | null;
  education_level: string | null;
  sections_found: string[];
}

export async function uploadResume(file: File, consent: boolean): Promise<ResumeUploadResult> {
  const form = new FormData();
  form.append('file', file);
  form.append('consent', String(consent));
  const response = await apiClient.post<ResumeUploadResult>('/resumes/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}
