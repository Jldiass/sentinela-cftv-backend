import { request } from "./client";
import type { AlarmEvent, EventInput } from "../types/api";
export const eventsApi = {
  list: (cameraId?: number) =>
    request<AlarmEvent[]>(`/events?limit=100${cameraId ? `&camera_id=${cameraId}` : ""}`),
  create: (cameraId: number, input: EventInput) =>
    request<AlarmEvent>(`/cameras/${cameraId}/events`, { method: "POST", body: JSON.stringify(input) }),
  get: (id: number) => request<AlarmEvent>(`/events/${id}`),
  remove: (id: number) => request<void>(`/events/${id}`, { method: "DELETE" }),
};
