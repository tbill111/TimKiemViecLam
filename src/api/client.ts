import axios from 'axios';

export const isOfflineDemo = import.meta.env.VITE_OFFLINE_DEMO === 'true';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
});

apiClient.interceptors.request.use((config) => {
  if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
    delete config.headers['Content-Type'];
    delete config.headers['content-type'];
  }
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
    const detail = error.response?.data as {
      detail?: string | { detail?: string; from?: string; to?: string } | Array<{ msg?: string }>;
    } | undefined;
    const detailValue = detail?.detail;
    if (typeof detailValue === 'string') return detailValue;
    if (Array.isArray(detailValue)) {
      return detailValue.map((item) => item.msg).filter(Boolean).join('; ') || fallback;
    }
    if (detailValue && typeof detailValue.detail === 'string') {
      if (detailValue.detail === 'invalid_transition') {
        const from = detailValue.from ?? 'hiện tại';
        const to = detailValue.to ?? 'mới';
        return `Không thể chuyển trạng thái từ "${from}" sang "${to}".`;
      }
      return detailValue.detail;
    }
  }
  return fallback;
}
