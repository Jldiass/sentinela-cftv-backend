import { useQuery } from "@tanstack/react-query";
import { camerasApi } from "../api/cameras";
import { HlsPlayer } from "../components/HlsPlayer";
import { apiMessage } from "../hooks/useApiError";
export function LivePage() {
  const cameras = useQuery({
    queryKey: ["cameras"],
    queryFn: () => camerasApi.list(false),
    refetchInterval: 12_000,
  });
  const active = cameras.data?.filter((camera) => camera.enabled) ?? [];
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">MONITORAMENTO</p>
          <h1>Ao vivo</h1>
          <p>Atualização automática a cada 12 segundos. Áudio inicia desativado.</p>
        </div>
        <span className="retention">HISTÓRICO: 1 HORA</span>
      </header>
      {cameras.isError ? (
        <div className="alert error">{apiMessage(cameras.error)}</div>
      ) : (
        <div className="live-grid">
          {active.map((camera) => (
            <HlsPlayer key={camera.id} camera={camera} />
          ))}
          {!active.length && <div className="empty">Não há câmeras habilitadas para exibir.</div>}
        </div>
      )}
    </>
  );
}
