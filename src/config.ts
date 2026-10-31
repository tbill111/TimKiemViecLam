/** Chế độ demo không cần backend: bật bằng VITE_OFFLINE_DEMO=true khi build/chạy. Mặc định là chế độ online (gọi API). */
export const OFFLINE = import.meta.env.VITE_OFFLINE_DEMO === 'true';

export const API_URL: string = import.meta.env.VITE_API_URL ?? '/api';

export const TOKEN_KEY = 'smartcareer_token';
export const USER_KEY = 'smartcareer_user';
