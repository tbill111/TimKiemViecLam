import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { isOfflineDemo } from '../api/client';
import { fetchCurrentUser, login as loginRequest, register as registerRequest, type AuthUser } from '../api/auth';

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<AuthUser>;
  register: (payload: Parameters<typeof registerRequest>[0]) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const DEMO_USER_KEY = 'smartcareer_demo_user';

/** Chế độ demo không có backend: giữ người dùng giả trong sessionStorage để tải lại trang không bị đăng xuất. */
function readDemoUser(): AuthUser | null {
  if (!isOfflineDemo) return null;
  try {
    const raw = sessionStorage.getItem(DEMO_USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(readDemoUser);
  const [loading, setLoading] = useState(!isOfflineDemo && Boolean(localStorage.getItem('smartcareer_token')));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOfflineDemo || !localStorage.getItem('smartcareer_token')) return;
    void fetchCurrentUser()
      .then(setUser)
      .catch(() => localStorage.removeItem('smartcareer_token'))
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    error,
    async login(email, password) {
      setLoading(true);
      setError(null);
      try {
        const nextUser = isOfflineDemo ? { id: 'demo', fullName: email, email, role: (email.startsWith('admin') ? 'admin' : email.startsWith('hr') ? 'recruiter' : 'candidate') as AuthUser['role'] } : await loginRequest(email, password);
        if (isOfflineDemo) sessionStorage.setItem(DEMO_USER_KEY, JSON.stringify(nextUser));
        setUser(nextUser);
        return nextUser;
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : 'Đăng nhập thất bại.');
        throw requestError;
      } finally {
        setLoading(false);
      }
    },
    async register(payload) {
      setLoading(true);
      setError(null);
      try {
        const nextUser = isOfflineDemo ? { id: 'demo', fullName: payload.fullName, email: payload.email, role: payload.role, companyName: payload.companyName } : await registerRequest(payload);
        if (isOfflineDemo) sessionStorage.setItem(DEMO_USER_KEY, JSON.stringify(nextUser));
        setUser(nextUser);
        return nextUser;
      } finally {
        setLoading(false);
      }
    },
    logout() {
      localStorage.removeItem('smartcareer_token');
      sessionStorage.removeItem(DEMO_USER_KEY);
      setUser(null);
    },
  }), [error, loading, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth phải được gọi bên trong AuthProvider');
  return context;
}
