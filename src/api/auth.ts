import { apiClient } from './client';

export interface AuthUser {
  id: string;
  fullName: string;
  email: string;
  role: 'candidate' | 'recruiter' | 'admin';
  companyName?: string;
}

interface AuthUserDto {
  id: string | number;
  email: string;
  role: AuthUser['role'];
  full_name: string;
  company_id?: number | null;
}

function adaptAuthUser(user: AuthUserDto): AuthUser {
  const companyName = localStorage.getItem(`smartcareer_company_${user.id}`) ?? undefined;
  return {
    id: String(user.id),
    email: user.email,
    role: user.role,
    fullName: user.full_name,
    companyName,
  };
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const response = await apiClient.post<{ access_token: string; user: AuthUserDto }>('/auth/login', { email, password });
  localStorage.setItem('smartcareer_token', response.data.access_token);
  return adaptAuthUser(response.data.user);
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const response = await apiClient.get<AuthUserDto>('/auth/me');
  return adaptAuthUser(response.data);
}

export async function register(payload: { email: string; password: string; fullName: string; role: AuthUser['role']; companyName?: string }): Promise<AuthUser> {
  const response = await apiClient.post<{ access_token: string; user: AuthUserDto }>('/auth/register', {
    email: payload.email,
    password: payload.password,
    role: payload.role,
    full_name: payload.fullName,
    company_name: payload.companyName,
  });
  localStorage.setItem('smartcareer_token', response.data.access_token);
  if (payload.companyName) localStorage.setItem(`smartcareer_company_${response.data.user.id}`, payload.companyName);
  return { ...adaptAuthUser(response.data.user), companyName: payload.companyName };
}
