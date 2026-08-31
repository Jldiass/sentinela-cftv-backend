import type { CameraStatus } from "../types/api";

export function CameraStatusBadge({ status }: { status: CameraStatus }) {
  const label = { online: "Online", unstable: "Instável", offline: "Offline" }[status];
  return (
    <span className={`status status-${status}`}>
      <i />
      {label}
    </span>
  );
}
export function ServiceStatus({ up }: { up: boolean }) {
  return (
    <span className={`status ${up ? "status-online" : "status-offline"}`}>
      <i />
      {up ? "Operante" : "Indisponível"}
    </span>
  );
}
