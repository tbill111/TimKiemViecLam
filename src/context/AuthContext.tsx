import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { authApi } from '../api/endpoints';
import type { Role, UserDTO } from '../api/dto';
import { OFFLINE, TOKEN_KEY, USER_KEY } from '../config';

interface AuthValue {
  user: UserDTO | null;
  /** false khi đang kiểm tra phiên đăng nhập lúc mở trang. */
  ready: boolean;
  login: (email: string, password: string) => Promise<UserDTO>;
  register: (body: { email: string; password: string; role: 'candidate' | 'recruiter'; full_name: string; company_name?: string }) => Promise<UserDTO>;
  logout: () => void;
}

const OFFLINE_USER: UserDTO = { id: 0, email: 'demo@smartcareer.vn', role: 'candidate', full_name: 'Giang Thanh Tùng', company_id: null };

const AuthContext = createContext<AuthValue | null>(null);

function readStoredUser(): UserDTO | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw && localStorage.getItem(TOKEN_KEY) ? (JSON.parse(raw) as UserDTO) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserDTO | null>(OFFLINE ? OFFLINE_USER : readStoredUser);
  const [ready, setReady] = useState(OFFLINE || !localStorage.getItem(TOKEN_KEY));

  // Kiểm tra token còn hiệu lực khi mở trang
  useEffect(() => {
    if (OFFLINE || ready) return;
    authApi
      .me()
      .then((u) => {
        setUser(u);
        localStorage.setItem(USER_KEY, JSON.stringify(u));
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        setUser(null);
      })
      .finally(() => setReady(true));
  }, [ready]);

  const store = useCallback((token: string, u: UserDTO) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(u));
    setUser(u);
    return u;
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    return store(res.access_token, res.user);
  }, [store]);

  const register = useCallback<AuthValue['register']>(async (body) => {
    const res = await authApi.register(body);
    return store(res.access_token, res.user);
  }, [store]);

  const logout = useCallback(() => {
    if (OFFLINE) return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, ready, login, register, logout }), [user, ready, login, register, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth phải nằm trong AuthProvider');
  return ctx;
}

/** Trang chủ theo vai trò sau khi đăng nhập. */
export function homePath(role: Role | undefined): string {
  return role === 'recruiter' || role === 'admin' ? '/employer/dashboard' : '/';
}
