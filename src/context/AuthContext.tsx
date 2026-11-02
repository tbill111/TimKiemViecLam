import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import { isOfflineDemo } from '../api/client';
import { login as loginRequest, register as registerRequest, type AuthUser } from '../api/auth';

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: Parameters<typeof registerRequest>[0]) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(
    isOfflineDemo
      ? { id: 'demo', fullName: 'Ngọc Anh', email: 'demo@smartcareer.local', role: 'candidate' }
      : null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    error,
    async login(email, password) {
      setLoading(true);
      setError(null);
      try {
        setUser(isOfflineDemo ? { id: 'demo', fullName: email, email, role: 'candidate' } : await loginRequest(email, password));
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
        setUser(isOfflineDemo ? { id: 'demo', fullName: payload.fullName, email: payload.email, role: payload.role, companyName: payload.companyName } : await registerRequest(payload));
      } finally {
        setLoading(false);
      }
    },
    logout() {
      localStorage.removeItem('smartcareer_token');
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
