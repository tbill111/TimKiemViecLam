import axios, { AxiosError } from 'axios';
import { API_URL, TOKEN_KEY, USER_KEY } from '../config';

export const api = axios.create({ baseURL: API_URL, timeout: 60_000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    // Token hết hạn hoặc không hợp lệ: xoá phiên và về trang đăng nhập
    const isLogin = error.config?.url?.includes('/auth/login');
    if (error.response?.status === 401 && !isLogin) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      if (!window.location.pathname.startsWith('/login')) window.location.assign('/login');
    }
    return Promise.reject(error);
  }
);

/** Thông điệp lỗi tiếng Việt cho người dùng từ lỗi API. */
const MESSAGES: Record<string, string> = {
  invalid_credentials: 'Email hoặc mật khẩu không đúng.',
  email_taken: 'Email này đã được đăng ký.',
  company_name_required: 'Nhà tuyển dụng cần nhập tên công ty.',
  already_applied: 'Bạn đã ứng tuyển vị trí này rồi.',
  job_closed: 'Tin tuyển dụng này đã đóng.',
  invalid_transition: 'Không thể chuyển sang trạng thái này (phải đi theo thứ tự các bước).',
  not_your_job: 'Tin tuyển dụng này không thuộc công ty của bạn.',
  consent_required: 'Bạn cần đồng ý cho hệ thống xử lý dữ liệu CV.',
  model_not_trained: 'Mô hình M4 chưa được huấn luyện. Hãy chọn M0–M3.',
  unsupported_type: 'Chỉ hỗ trợ tệp PDF, DOCX hoặc TXT.',
  too_large: 'Tệp lớn hơn 5 MB.',
  no_text: 'Không đọc được chữ trong CV (có thể là ảnh scan).',
  corrupt: 'Tệp CV bị hỏng hoặc không hợp lệ.',
  superset_not_configured: 'Superset chưa được cấu hình.',
  superset_unavailable: 'Không kết nối được Superset.',
  candidate_profile_not_found: 'Chưa có hồ sơ ứng viên.',
  salary_min_greater_than_max: 'Lương tối thiểu không được lớn hơn lương tối đa.',
};

interface ApiDetail {
  detail?: string;
  skills?: string[];
}

function detailOf(error: unknown): { code?: string; extra?: ApiDetail; status?: number; raw?: unknown } {
  if (!axios.isAxiosError(error) || !error.response) return {};
  const raw = error.response.data?.detail as string | ApiDetail | unknown[] | undefined;
  if (typeof raw === 'string') return { code: raw, status: error.response.status, raw };
  if (raw && !Array.isArray(raw)) return { code: (raw as ApiDetail).detail, extra: raw as ApiDetail, status: error.response.status, raw };
  return { status: error.response.status, raw };
}

export function errorCode(error: unknown): string | undefined {
  return detailOf(error).code;
}

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error) && !error.response) {
    return 'Không kết nối được máy chủ. Kiểm tra backend hoặc bật chế độ demo (VITE_OFFLINE_DEMO=true).';
  }
  const { code, extra, status, raw } = detailOf(error);
  if (code === 'unknown_skills') return `Kỹ năng không có trong danh mục: ${(extra?.skills ?? []).join(', ')}.`;
  if (code && MESSAGES[code]) return MESSAGES[code];
  if (status === 403) return 'Bạn không có quyền thực hiện thao tác này.';
  if (status === 422 && Array.isArray(raw)) return 'Dữ liệu chưa hợp lệ, vui lòng kiểm tra lại các trường.';
  if (code) return code;
  return error instanceof Error ? error.message : 'Đã xảy ra lỗi.';
}
