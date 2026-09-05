export type CameraStatus = "online" | "unstable" | "offline";
export type ClipStatus = "pending" | "available" | "expired";

export interface Camera {
  id: number;
  name: string;
  location: string;
  audio_enabled: boolean;
  pre_alarm_seconds: number;
  post_alarm_seconds: number;
  enabled: boolean;
  created_at: string;
  status: CameraStatus;
  hls_url: string;
  effective_retention_hours: number;
}
export interface CameraInput {
  name: string;
  location?: string;
  audio_enabled?: boolean;
  pre_alarm_seconds?: number;
  post_alarm_seconds?: number;
}
export interface CameraUpdate extends Partial<CameraInput> {
  enabled?: boolean;
}
export interface StreamCredentials {
  camera_id: number;
  stream_key: string;
  stream_path: string;
  rtmp_server_url: string;
  rtmp_url: string;
  hls_url: string;
}
export interface Recording {
  start: string;
  duration: number;
  url: string;
}
export interface AlarmEvent {
  id: number;
  camera_id: number;
  kind: string;
  note: string;
  happened_at: string;
  clip_start: string;
  clip_duration: number;
  playback_url: string | null;
  clip_status: ClipStatus;
  available_until: string;
}
export interface EventInput {
  kind?: string;
  note?: string;
  happened_at?: string;
}
export interface Health {
  ok: boolean;
  database: "up" | "down";
  mediamtx: "up" | "down";
  active_streams: number;
  version: string;
  effective_retention_hours: number;
}
export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
  roles: string[];
  permissions: string[];
}
export interface AuthTokens {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: AuthUser;
}
export interface Role {
  id: number;
  name: string;
  description: string;
  permission_codes: string[];
  is_system: boolean;
  user_count: number;
  created_at: string;
}
export interface Permission {
  id: number;
  code: string;
  description: string;
}
export interface UserRecord extends AuthUser {
  updated_at: string;
}
export interface UserInput {
  full_name: string;
  email: string;
  password?: string;
  is_active: boolean;
  role_ids: number[];
}
export interface RoleInput {
  name: string;
  description: string;
  permission_codes: string[];
}
export interface MosaicCamera {
  camera_id: number;
  position: number;
  camera: Camera;
}
export interface MosaicCameraInput {
  camera_id: number;
  position: number;
}
export interface Mosaic {
  id: number;
  name: string;
  capacity: number;
  columns: number;
  rows: number;
  active: boolean;
  camera_count: number;
  user_count: number;
  cameras: MosaicCamera[];
  user_ids: number[];
  role_ids: number[];
  created_at: string;
  updated_at: string;
}
export interface MosaicInput {
  name: string;
  capacity: number;
  active: boolean;
  cameras: MosaicCameraInput[];
  user_ids: number[];
  role_ids: number[];
}
export interface CameraStatusSummary {
  online: number;
  unstable: number;
  offline: number;
  total: number;
  generated_at: string;
}
export interface CameraStatusPeriod {
  id: number;
  camera_id: number;
  camera_name: string;
  status: CameraStatus;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
}
export interface ApiErrorPayload {
  detail?: string | Array<{ loc: Array<string | number>; msg: string; type: string }>;
}
