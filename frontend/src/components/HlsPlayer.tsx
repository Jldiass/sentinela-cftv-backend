import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";
import { Radio } from "lucide-react";
import type { Camera } from "../types/api";
import { CameraStatusBadge } from "./Status";

export function HlsPlayer({ camera, compact = false }: { camera: Camera; compact?: boolean }) {
  const video = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState(false);
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
    if (!Hls.isSupported()) {
      setError(true);
      return;
    }
    const hls = new Hls({ enableWorker: true, lowLatencyMode: true });
    hls.loadSource(camera.hls_url);
    hls.attachMedia(element);
    hls.on(Hls.Events.ERROR, (_, data) => {
      if (data.fatal) setError(true);
    });
    return () => hls.destroy();
  }, [camera.hls_url, camera.status]);
  return (
    <article className={`video-panel ${compact ? "video-compact" : ""}`}>
      <header>
        <div>
          <strong>{camera.name}</strong>
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
          muted
          autoPlay
          playsInline
          controls={false}
          aria-label={`Vídeo ao vivo: ${camera.name}`}
        />
      )}
    </article>
  );
}
