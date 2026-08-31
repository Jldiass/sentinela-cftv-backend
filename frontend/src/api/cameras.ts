import { request } from "./client";
import type { Camera, CameraInput, CameraUpdate, Recording, StreamCredentials } from "../types/api";
export const camerasApi = {
  list: (includeDisabled = true) => request<Camera[]>(`/cameras?include_disabled=${includeDisabled}`),
  get: (id: number) => request<Camera>(`/cameras/${id}`),
  create: (input: CameraInput) =>
    request<Camera>("/cameras", { method: "POST", body: JSON.stringify(input) }),
  update: (id: number, input: CameraUpdate) =>
    request<Camera>(`/cameras/${id}`, { method: "PATCH", body: JSON.stringify(input) }),
  remove: (id: number) => request<void>(`/cameras/${id}`, { method: "DELETE" }),
  stream: (id: number) => request<StreamCredentials>(`/cameras/${id}/stream`),
  rotateKey: (id: number) =>
    request<StreamCredentials>(`/cameras/${id}/stream-key/rotate`, { method: "POST" }),
  recordings: (id: number, start: string, end: string) =>
    request<Recording[]>(
      `/cameras/${id}/recordings?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`,
    ),
};
