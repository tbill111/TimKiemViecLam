import { apiClient } from './client';

export interface AuthUser {
  id: string;
  fullName: string;
  email: string;
  role: 'candidate' | 'recruiter' | 'admin';
  companyName?: string;
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const response = await apiClient.post<{ access_token: string; user: AuthUser }>('/auth/login', { email, password });
  localStorage.setItem('smartcareer_token', response.data.access_token);
  return response.data.user;
}

export async function register(payload: { email: string; password: string; fullName: string; role: AuthUser['role']; companyName?: string }): Promise<AuthUser> {
  const response = await apiClient.post<AuthUser>('/auth/register', payload);
  return response.data;
}
