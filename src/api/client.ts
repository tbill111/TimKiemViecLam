import axios from 'axios';

export const isOfflineDemo = import.meta.env.VITE_OFFLINE_DEMO === 'true';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('smartcareer_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      localStorage.removeItem('smartcareer_token');
      if (window.location.pathname !== '/login') window.location.assign('/login');
    }
    return Promise.reject(error);
  }
);

export function apiErrorMessage(error: unknown, fallback = 'Không thể kết nối máy chủ.') {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data as { detail?: string | { detail?: string } } | undefined;
    if (typeof detail?.detail === 'string') return detail.detail;
    if (detail?.detail && typeof detail.detail === 'object' && typeof detail.detail.detail === 'string') {
      return detail.detail.detail;
    }
  }
  return fallback;
}
