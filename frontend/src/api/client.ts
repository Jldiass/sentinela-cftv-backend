import type { ApiErrorPayload } from "../types/api";

export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
export const API_ORIGIN = API_URL.replace(/\/api\/v1\/?$/, "");
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
  if (Array.isArray(payload.detail)) return payload.detail.map((item) => item.msg).join("; ");
  return (
    {
      404: "O recurso solicitado não foi encontrado.",
      409: "A operação conflita com o estado atual da câmera.",
      422: "Revise os dados informados.",
      503: "O serviço de mídia está indisponível no momento.",
    }[status] ?? "Não foi possível concluir a operação."
  );
}
async function requestFrom<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new ApiError(response.status, payload);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export const request = <T>(path: string, init?: RequestInit) => requestFrom<T>(API_URL, path, init);
export const requestRoot = <T>(path: string, init?: RequestInit) => requestFrom<T>(API_ORIGIN, path, init);
