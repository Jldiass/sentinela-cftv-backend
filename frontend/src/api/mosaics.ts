import type { Mosaic, MosaicInput } from "../types/api";
import { request } from "./client";

export const mosaicsApi = {
  list: (search = "", includeInactive = false) => {
    const query = new URLSearchParams();
    if (search) query.set("search", search);
    if (includeInactive) query.set("include_inactive", "true");
    const suffix = query.size ? `?${query.toString()}` : "";
    return request<Mosaic[]>(`/mosaics${suffix}`);
  },
  get: (id: number) => request<Mosaic>(`/mosaics/${id}`),
  view: (id: number) => request<Mosaic>(`/mosaics/${id}/view`),
  create: (input: MosaicInput) =>
    request<Mosaic>("/mosaics", { method: "POST", body: JSON.stringify(input) }),
  update: (id: number, input: Partial<MosaicInput>) =>
    request<Mosaic>(`/mosaics/${id}`, { method: "PATCH", body: JSON.stringify(input) }),
  remove: (id: number) => request<void>(`/mosaics/${id}`, { method: "DELETE" }),
};
