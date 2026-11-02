import type { Application } from '../types';
import { apiClient } from './client';
import { adaptApplication } from './adapters';
import type { ApplicationDto } from './dto';

export async function fetchApplications(): Promise<Application[]> {
  const response = await apiClient.get<ApplicationDto[]>('/applications');
  return response.data.map(adaptApplication);
}

export async function createApplication(jobId: string): Promise<Application> {
  const response = await apiClient.post<ApplicationDto>('/applications', { job_id: jobId });
  return adaptApplication(response.data);
}

export async function updateApplicationStatus(id: string, status: string): Promise<Application> {
  const response = await apiClient.patch<ApplicationDto>(`/applications/${id}/status`, { status });
  return adaptApplication(response.data);
}
