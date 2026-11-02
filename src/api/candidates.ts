import type { StudentProfile } from '../types';
import { apiClient } from './client';

export async function fetchProfile(): Promise<StudentProfile> {
  const response = await apiClient.get<StudentProfile>('/candidates/me');
  return response.data;
}

export async function updateProfile(profile: Partial<StudentProfile>): Promise<StudentProfile> {
  const response = await apiClient.put<StudentProfile>('/candidates/me', profile);
  return response.data;
}
