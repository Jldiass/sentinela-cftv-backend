export type CameraStatus = "online" | "unstable" | "offline";
export type ClipStatus = "pending" | "available" | "expired";
export interface Camera {
  id: number;
  name: string;
  location: string;
  audio_enabled: boolean;
  pre_alarm_seconds: number;
  post_alarm_seconds: number;
  stream_key: string;
  stream_path: string;
  enabled: boolean;
  created_at: string;
  status: CameraStatus;
  rtmp_server_url: string;
  rtmp_url: string;
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
export interface ApiErrorPayload {
  detail?: string | Array<{ loc: Array<string | number>; msg: string; type: string }>;
}
