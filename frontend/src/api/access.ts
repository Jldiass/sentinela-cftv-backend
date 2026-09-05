import type { Permission, Role, RoleInput, UserInput, UserRecord } from "../types/api";
import { request } from "./client";

export const accessApi = {
  users: () => request<UserRecord[]>("/users"),
  createUser: (input: UserInput) =>
    request<UserRecord>("/users", { method: "POST", body: JSON.stringify(input) }),
  updateUser: (id: number, input: Partial<UserInput>) =>
    request<UserRecord>(`/users/${id}`, { method: "PATCH", body: JSON.stringify(input) }),
  removeUser: (id: number) => request<void>(`/users/${id}`, { method: "DELETE" }),
  roles: () => request<Role[]>("/roles"),
  createRole: (input: RoleInput) => request<Role>("/roles", { method: "POST", body: JSON.stringify(input) }),
  updateRole: (id: number, input: Partial<RoleInput>) =>
    request<Role>(`/roles/${id}`, { method: "PATCH", body: JSON.stringify(input) }),
  removeRole: (id: number) => request<void>(`/roles/${id}`, { method: "DELETE" }),
  permissions: () => request<Permission[]>("/permissions"),
};
