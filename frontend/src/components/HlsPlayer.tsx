import { useEffect, useRef, useState } from "react";
import { Radio, Volume2, VolumeX } from "lucide-react";
import type { Camera } from "../types/api";
import { CameraStatusBadge } from "./Status";

export function HlsPlayer({
  camera,
  compact = false,
  position,
}: {
  camera: Camera;
  compact?: boolean;
  position?: number;
}) {
  const video = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState(false);
  const [muted, setMuted] = useState(true);
  useEffect(() => {
    const element = video.current;
    if (!element || camera.status === "offline") return;
    setError(false);
    if (element.canPlayType("application/vnd.apple.mpegurl")) {
      element.src = camera.hls_url;
      return () => {
        element.removeAttribute("src");
        element.load();
      };
    }
    let disposed = false;
    let destroy: (() => void) | undefined;
    void import("hls.js")
      .then(({ default: Hls }) => {
        if (disposed) return;
        if (!Hls.isSupported()) {
          setError(true);
          return;
        }
        const hls = new Hls({ enableWorker: true, lowLatencyMode: true });
        destroy = () => hls.destroy();
        hls.loadSource(camera.hls_url);
        hls.attachMedia(element);
        hls.on(Hls.Events.ERROR, (_, data) => {
          if (data.fatal) setError(true);
        });
      })
      .catch(() => setError(true));
    return () => {
      disposed = true;
      destroy?.();
    };
  }, [camera.hls_url, camera.status]);
  return (
    <article className={`video-panel ${compact ? "video-compact" : ""}`}>
      <header>
        <div>
          <strong>{position ? `${position}. ${camera.name}` : camera.name}</strong>
          <small>{camera.location || "Local não informado"}</small>
        </div>
        <CameraStatusBadge status={camera.status} />
      </header>
      {camera.status === "offline" || error ? (
        <div className="video-offline">
          <Radio size={28} />
          <span>{error ? "Sinal indisponível" : "Câmera offline"}</span>
        </div>
      ) : (
        <video
          ref={video}
          muted={muted}
          autoPlay
          playsInline
          controls={false}
          aria-label={`Vídeo ao vivo: ${camera.name}`}
        />
      )}
      {camera.status !== "offline" && !error && camera.audio_enabled && (
        <button
          className="video-audio"
          onClick={() => setMuted((value) => !value)}
          aria-label={muted ? `Ativar áudio de ${camera.name}` : `Desativar áudio de ${camera.name}`}
        >
          {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          {muted ? "Ativar áudio" : "Silenciar"}
        </button>
      )}
    </article>
  );
}
