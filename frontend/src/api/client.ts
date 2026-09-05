import type { ApiErrorPayload, AuthTokens } from "../types/api";
export const API_URL = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "");
export const API_ORIGIN = API_URL.replace(/\/api\/v1\/?$/, "");
let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;
let onUnauthorized: (() => void) | null = null;
export function setAccessToken(token: string | null) {
  accessToken = token;
}
export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}
export class ApiError extends Error {
  status: number;
  payload: ApiErrorPayload;
  constructor(status: number, payload: ApiErrorPayload) {
    super(messageFromPayload(status, payload));
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}
export function messageFromPayload(status: number, payload: ApiErrorPayload): string {
  if (typeof payload.detail === "string") return payload.detail;
  if (Array.isArray(payload.detail)) return payload.detail.map((i) => i.msg).join("; ");
  return (
    {
      401: "Sua sessão expirou. Entre novamente.",
      403: "Seu perfil não permite esta operação.",
      404: "O recurso solicitado não foi encontrado.",
      409: "A operação conflita com o estado atual do recurso.",
      422: "Revise os dados informados.",
      503: "O serviço está indisponível no momento.",
    }[status] ?? "Não foi possível concluir a operação."
  );
}
async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    })
      .then(async (response) => {
        if (!response.ok) return null;
        const tokens = (await response.json()) as AuthTokens;
        setAccessToken(tokens.access_token);
        return tokens.access_token;
      })
      .catch(() => null)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}
async function requestFrom<T>(baseUrl: string, path: string, init?: RequestInit, retry = true): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type") && init?.body) headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(`${baseUrl}${path}`, { ...init, headers, credentials: "include" });
  if (response.status === 401 && retry && path !== "/auth/login" && path !== "/auth/refresh") {
    const token = await refreshAccessToken();
    if (token) return requestFrom<T>(baseUrl, path, init, false);
    accessToken = null;
    onUnauthorized?.();
  }
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new ApiError(response.status, payload);
  }
  if (response.status === 204) return undefined as T;
  if (!response.headers.get("Content-Type")?.includes("application/json"))
    return response.blob() as Promise<T>;
  return response.json() as Promise<T>;
}
export const request = <T>(path: string, init?: RequestInit) => requestFrom<T>(API_URL, path, init);
export const requestRoot = <T>(path: string, init?: RequestInit) => requestFrom<T>(API_ORIGIN, path, init);
export const tryRefresh = refreshAccessToken;
