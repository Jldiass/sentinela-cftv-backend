import { request, setAccessToken } from "./client";
import type { AuthTokens, AuthUser } from "../types/api";
export const authApi = {
  register: async (email: string, fullName: string, password: string) => {
    const tokens = await request<AuthTokens>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, full_name: fullName, password }),
    });
    setAccessToken(tokens.access_token);
    return tokens;
  },
  login: async (email: string, password: string) => {
    const tokens = await request<AuthTokens>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setAccessToken(tokens.access_token);
    return tokens;
  },
  me: () => request<AuthUser>("/auth/me"),
  forgotPassword: (email: string) =>
    request<{ message: string }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  resetPassword: (token: string, newPassword: string) =>
    request<{ message: string }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword }),
    }),
  logout: async () => {
    try {
      await request<void>("/auth/logout", { method: "POST" });
    } finally {
      setAccessToken(null);
    }
  },
};
