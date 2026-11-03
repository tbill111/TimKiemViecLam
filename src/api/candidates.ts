import type { StudentProfile } from '../types';
import { apiClient } from './client';
import { adaptMatch } from './adapters';
import type { MatchDto } from './dto';

export async function fetchProfile(): Promise<StudentProfile> {
  const response = await apiClient.get<StudentProfile>('/candidates/me');
  return response.data;
}

export async function updateProfile(profile: Partial<StudentProfile>): Promise<StudentProfile> {
  if (profile.skills) {
    await updateSkills(profile.skills);
  }
  const response = await apiClient.put<StudentProfile>('/candidates/me', profile);
  return { ...profile, ...response.data } as StudentProfile;
}

export async function updateSkills(skills: string[]): Promise<string[]> {
  const response = await apiClient.put<{ skills: string[] }>('/candidates/me/skills', { skills });
  return response.data.skills;
}

export async function fetchRecommendations(): Promise<Array<{ jobId: string; match: ReturnType<typeof adaptMatch> }>> {
  const response = await apiClient.get<{ items: Array<{ job_id: string | number; match: MatchDto }> }>('/candidates/me/recommendations', { params: { top: 10, model: 'm3' } });
  return response.data.items.map((item) => ({ jobId: String(item.job_id), match: adaptMatch(String(item.job_id), item.match) }));
}
export async function fetchMatches(): Promise<Array<{ jobId: string; match: ReturnType<typeof adaptMatch> }>> {
  const response = await apiClient.get<{ items: Array<{ job_id: string | number; match: MatchDto }> }>('/candidates/me/matches', { params: { model: 'm3' } });
  return response.data.items.map((item) => ({ jobId: String(item.job_id), match: adaptMatch(String(item.job_id), item.match) }));
}
