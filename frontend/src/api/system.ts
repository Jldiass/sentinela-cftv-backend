import { requestRoot } from "./client";
import type { Health } from "../types/api";
export const systemApi = { health: () => requestRoot<Health>("/health") };
