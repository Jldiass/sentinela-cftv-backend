import { request } from "./client";
import type { CameraStatus, CameraStatusPeriod, CameraStatusSummary } from "../types/api";
export interface StatusFilters {
  cameraId?: number;
  status?: CameraStatus | "";
  from?: string;
  to?: string;
}
export const cameraStatusApi = {
  summary: () => request<CameraStatusSummary>("/camera-status/summary"),
  history: (filters: StatusFilters) => {
    const query = new URLSearchParams();
    if (filters.cameraId) query.set("camera_id", String(filters.cameraId));
    if (filters.status) query.set("status", filters.status);
    if (filters.from) query.set("from", new Date(filters.from).toISOString());
    if (filters.to) query.set("to", new Date(filters.to).toISOString());
    return request<CameraStatusPeriod[]>(`/camera-status/history?${query}`);
  },
  report: (filters: StatusFilters) => {
    const query = new URLSearchParams();
    if (filters.cameraId) query.set("camera_id", String(filters.cameraId));
    if (filters.status) query.set("status", filters.status);
    if (filters.from) query.set("from", new Date(filters.from).toISOString());
    if (filters.to) query.set("to", new Date(filters.to).toISOString());
    return request<Blob>(`/camera-status/report?${query}`);
  },
};
