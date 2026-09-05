import { History, MapPin, Volume2 } from "lucide-react";
import type { Camera } from "../types/api";
import { CameraStatusBadge } from "./Status";

export function CameraDetails({ camera }: { camera: Camera }) {
  return (
    <div className="details-panel">
      <div className="details-title">
        <div>
          <p className="eyebrow">Câmera #{camera.id}</p>
          <h3>{camera.name}</h3>
        </div>
        <CameraStatusBadge status={camera.status} />
      </div>
      <dl className="detail-grid">
        <div>
          <dt>
            <MapPin size={14} /> Localização
          </dt>
          <dd>{camera.location || "Não informada"}</dd>
        </div>
        <div>
          <dt>
            <Volume2 size={14} /> Áudio
          </dt>
          <dd>{camera.audio_enabled ? "Habilitado" : "Desativado"}</dd>
        </div>
        <div>
          <dt>PRÉ-ALARME</dt>
          <dd>{camera.pre_alarm_seconds} segundos</dd>
        </div>
        <div>
          <dt>PÓS-ALARME</dt>
          <dd>{camera.post_alarm_seconds} segundos</dd>
        </div>
        <div>
          <dt>
            <History size={14} /> Retenção
          </dt>
          <dd>{camera.effective_retention_hours} hora</dd>
        </div>
      </dl>
      <p className="detail-note">
        As credenciais RTMP são protegidas. Use o botão RTMP na lista quando precisar configurar o
        equipamento.
      </p>
    </div>
  );
}
