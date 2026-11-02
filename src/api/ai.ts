import { apiClient } from './client';
import { adaptMatch } from './adapters';
import type { SkillMatchResult } from '../types';
import type { MatchDto } from './dto';

export async function matchJob(jobId: string, model = 'm3'): Promise<SkillMatchResult> {
  const response = await apiClient.post<MatchDto>('/ai/match', { job_id: jobId, model });
  return adaptMatch(jobId, response.data);
}
