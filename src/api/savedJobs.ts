import { apiClient } from './client';
import type { SavedJob } from '../types';

export async function fetchSavedJobs(): Promise<SavedJob[]> {
  const response = await apiClient.get<{ items: Array<{ job_id: string; saved_at: string }> }>('/saved-jobs');
  return response.data.items.map((item) => ({ jobId: String(item.job_id), savedAt: item.saved_at }));
}

export async function saveJob(jobId: string): Promise<void> {
  await apiClient.post(`/saved-jobs/${jobId}`);
}

export async function unsaveJob(jobId: string): Promise<void> {
  await apiClient.delete(`/saved-jobs/${jobId}`);
}
