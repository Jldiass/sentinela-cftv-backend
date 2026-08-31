import { Copy, KeyRound, MapPin, Volume2 } from "lucide-react";
import { useState } from "react";
import type { Camera } from "../types/api";
import { CameraStatusBadge } from "./Status";

export function CameraDetails({ camera }: { camera: Camera }) {
  const [copied, setCopied] = useState<"url" | "server" | "key" | null>(null);
  const copy = async (kind: "url" | "server" | "key", value: string) => {
    await navigator.clipboard.writeText(value);
    setCopied(kind);
    window.setTimeout(() => setCopied(null), 1800);
  };
  return (
    <div className="details-panel">
      <div className="details-title">
        <div>
          <p className="eyebrow">CÂMERA #{camera.id}</p>
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
      </dl>
      <p className="detail-note">
        <KeyRound size={15} /> No Mibo, apague o conteúdo antigo e cole somente a URL completa.
      </p>
      <strong>URL para Mibo</strong>
      <div className="credential-value">
        <code>{camera.rtmp_url}</code>
        <button
          className="icon-button"
          onClick={() => copy("url", camera.rtmp_url)}
          aria-label="Copiar URL RTMP completa"
        >
          <Copy size={17} />
        </button>
      </div>
      <strong>Servidor RTMP</strong>
      <div className="credential-value">
        <code>{camera.rtmp_server_url}</code>
        <button
          className="icon-button"
          onClick={() => copy("server", camera.rtmp_server_url)}
          aria-label="Copiar servidor RTMP"
        >
          <Copy size={17} />
        </button>
      </div>
      <strong>Chave do stream</strong>
      <div className="credential-value">
        <code>{camera.stream_key}</code>
        <button
          className="icon-button"
          onClick={() => copy("key", camera.stream_key)}
          aria-label="Copiar chave do stream"
        >
          <Copy size={17} />
        </button>
      </div>
      {copied && (
        <span className="copy-state">
          {copied === "url" ? "URL completa" : copied === "server" ? "Servidor" : "Chave"} copiado(a)
        </span>
      )}
    </div>
  );
}
