import { ApiError } from "../api/client";
export function apiMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "Falha de comunicação com a API. Verifique se o backend está ativo.";
}
