import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { authApi } from "../api/auth";
import { setAccessToken, setUnauthorizedHandler, tryRefresh } from "../api/client";
import type { AuthUser } from "../types/api";
import { AuthContext } from "./useAuth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);
  const clearSession = useCallback(() => {
    setAccessToken(null);
    setUser(null);
  }, []);
  useEffect(() => {
    setUnauthorizedHandler(clearSession);
    return () => setUnauthorizedHandler(null);
  }, [clearSession]);
  useEffect(() => {
    let active = true;
    void tryRefresh()
      .then(async (token) => {
        if (!active || !token) return;
        try {
          const current = await authApi.me();
          if (active) setUser(current);
        } catch {
          clearSession();
        }
      })
      .finally(() => {
        if (active) setReady(true);
      });
    return () => {
      active = false;
    };
  }, [clearSession]);
  const login = useCallback(async (email: string, password: string) => {
    const session = await authApi.login(email, password);
    setUser(session.user);
    return session.user;
  }, []);
  const register = useCallback(async (email: string, fullName: string, password: string) => {
    const session = await authApi.register(email, fullName, password);
    setUser(session.user);
    return session.user;
  }, []);
  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);
  const can = useCallback((permission: string) => Boolean(user?.permissions.includes(permission)), [user]);
  const value = useMemo(
    () => ({ user, ready, login, register, logout, can }),
    [user, ready, login, register, logout, can],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
