import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { camerasApi } from "../api/cameras";
import { systemApi } from "../api/system";
import { HlsPlayer } from "../components/HlsPlayer";
import { apiMessage } from "../hooks/useApiError";
export function OverviewPage() {
  const cameras = useQuery({
    queryKey: ["cameras"],
    queryFn: () => camerasApi.list(false),
    refetchInterval: 12_000,
  });
  const health = useQuery({ queryKey: ["health"], queryFn: systemApi.health, refetchInterval: 15_000 });
  const online = cameras.data?.filter((camera) => camera.status !== "offline") ?? [];
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">CENTRAL OPERACIONAL</p>
          <h1>Visão geral</h1>
          <p>Estado atual da infraestrutura e dos canais de vídeo.</p>
        </div>
        <Link className="button primary" to="/cameras">
          Gerenciar câmeras
        </Link>
      </header>
      <section className="metric-grid">
        <div className="metric">
          <small>CÂMERAS ATIVAS</small>
          <strong>
            {cameras.data?.filter((camera) => camera.enabled).length ?? "--"}
            <i>/ 8</i>
          </strong>
        </div>
        <div className="metric">
          <small>SINAIS ONLINE</small>
          <strong>{online.length}</strong>
        </div>
        <div className="metric">
          <small>STREAMS ATIVOS</small>
          <strong>{health.data?.active_streams ?? "--"}</strong>
        </div>
        <div className="metric">
          <small>HISTÓRICO</small>
          <strong>
            {health.data?.effective_retention_hours ?? 1}
            <i> hora</i>
          </strong>
        </div>
      </section>
      {health.isError && <div className="alert error">{apiMessage(health.error)}</div>}
      <section className="section-head">
        <div>
          <p className="eyebrow">PRIORIDADE</p>
          <h2>Canais em operação</h2>
        </div>
        <Link to="/live">Abrir mosaico</Link>
      </section>
      {cameras.isError ? (
        <div className="alert error">{apiMessage(cameras.error)}</div>
      ) : (
        <div className="overview-video-grid">
          {online.slice(0, 4).map((camera) => (
            <HlsPlayer key={camera.id} camera={camera} compact />
          ))}
          {!online.length && <div className="empty">Nenhum canal online no momento.</div>}
        </div>
      )}
    </>
  );
}
