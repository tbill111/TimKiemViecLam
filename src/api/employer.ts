import { apiClient } from './client';
import { adaptJob } from './adapters';
import type { Job, ApplicationStatus } from '../types';

export async function fetchEmployerJobs(): Promise<Job[]> {
  const response = await apiClient.get<{ items: unknown[] }>('/jobs', { params: { mine: 'true', page_size: '100' } });
  return response.data.items
    .map((item) => adaptJob(item as Parameters<typeof adaptJob>[0]))
    .filter((job) => job.status !== 'closed');
}
export async function createJob(payload: Record<string, unknown>): Promise<Job> {
  const response = await apiClient.post<Parameters<typeof adaptJob>[0]>('/jobs', payload);
  return adaptJob(response.data);
}
export async function updateJob(id: string, payload: Record<string, unknown>): Promise<Job> {
  const response = await apiClient.put<Parameters<typeof adaptJob>[0]>(`/jobs/${id}`, { ...payload, id });
  return adaptJob(response.data);
}
export async function closeJob(id: string): Promise<void> { await apiClient.delete(`/jobs/${id}`); }

export interface RankedCandidate {
  candidate_id: number;
  full_name: string;
  application_id: number;
  status: string;
  applied_at: string;
  match: { total_score: number; matched_required: string[]; missing_required: string[]; explanation: string };
}
export async function fetchRankedCandidates(jobId: string): Promise<RankedCandidate[]> {
  const response = await apiClient.get<{ items: RankedCandidate[] }>(`/jobs/${jobId}/ranked-candidates`);
  return response.data.items;
}
const statusApi: Record<ApplicationStatus, string> = {
  'Đã ứng tuyển': 'applied', 'Đang xem xét': 'screening', 'Phỏng vấn': 'interview',
  'Đề nghị nhận việc': 'offer', 'Đã nhận việc': 'hired', 'Đã từ chối': 'rejected',
};
export async function moveApplication(id: number, status: ApplicationStatus): Promise<void> {
  await apiClient.patch(`/applications/${id}/status`, { status: statusApi[status] });
}
