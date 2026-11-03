import { apiClient } from './client';

export interface BiSummary { candidates: number; open_jobs: number; applications: number; hire_rate: number }
export interface BiRow { [key: string]: string | number | null }
export interface BiGuestToken { token: string; dashboard_id?: string; superset_domain?: string }

export async function fetchBiSummary(): Promise<BiSummary> {
  const response = await apiClient.get<BiSummary>('/bi/summary');
  return response.data;
}
export async function fetchBiData(path: 'skills' | 'salary' | 'funnel'): Promise<{ items: BiRow[]; stages?: BiRow[] }> {
  const response = await apiClient.get<{ items: BiRow[]; stages?: BiRow[] }>(`/bi/${path}`);
  return response.data;
}
export async function fetchBiGuestToken(): Promise<BiGuestToken> {
  const response = await apiClient.get<BiGuestToken>('/bi/guest-token');
  return response.data;
}
