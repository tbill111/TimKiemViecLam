import type { Job } from '../types';
import { apiClient } from './client';
import type { JobsResponseDto } from './dto';
import { adaptJob } from './adapters';

export async function fetchJobs(params?: Record<string, string>): Promise<Job[]> {
  const response = await apiClient.get<JobsResponseDto | { items: unknown[] } | unknown[]>('/jobs', {
    params: { page_size: '100', ...params },
  });
  const items = Array.isArray(response.data) ? response.data : response.data.items;
  return items.map((item) => adaptJob(item as Parameters<typeof adaptJob>[0]));
}
