"use client";
import * as React from "react";
import { api } from "@/lib/api";
import { getAccessToken, setTokens, clearTokens } from "@/lib/storage";
import type { AuthTokens } from "@/lib/api";

interface AuthContextValue {
  user: any | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: {
    email: string; username: string; password: string; full_name?: string;
  }) => Promise<void>;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<any | null>(null);
  const [loading, setLoading] = React.useState(true);

  // Restore session from stored token on mount
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!getAccessToken()) { if (!cancelled) setLoading(false); return; }
      try {
        const me = await api.me();
        if (!cancelled) setUser(me);
      } catch {
        clearTokens();
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const login = async (email: string, password: string) => {
    const tokens: AuthTokens = await api.login(email, password);
    setTokens(tokens);
    const me = await api.me();
    setUser(me);
  };

  const register = async (payload: {
    email: string; username: string; password: string; full_name?: string;
  }) => {
    await api.register(payload);
    await login(payload.email, payload.password);
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
