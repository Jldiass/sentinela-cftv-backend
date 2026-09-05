import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { useState } from "react";
import { camerasApi } from "../api/cameras";
import { apiMessage } from "../hooks/useApiError";
const now = new Date();
const hourAgo = new Date(now.getTime() - 60 * 60 * 1000);
export function HistoryPage() {
  const cameras = useQuery({ queryKey: ["cameras"], queryFn: () => camerasApi.list(false) });
  const [cameraId, setCameraId] = useState<number | "">("");
  const [start, setStart] = useState(hourAgo.toISOString().slice(0, 16));
  const [end, setEnd] = useState(now.toISOString().slice(0, 16));
  const recordings = useQuery({
    queryKey: ["recordings", cameraId, start, end],
    queryFn: () =>
      camerasApi.recordings(Number(cameraId), new Date(start).toISOString(), new Date(end).toISOString()),
    enabled: Boolean(cameraId) && new Date(start) < new Date(end),
  });
  const retention = cameras.data?.[0]?.effective_retention_hours;
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">ARQUIVO OPERACIONAL</p>
          <h1>Histórico</h1>
          <p>Consulta limitada à janela móvel definida pela central.</p>
        </div>
        <span className="retention">HISTÓRICO: {retention ? `${retention}H` : "--"}</span>
      </header>
      <section className="filter-panel">
        <label>
          Câmera
          <select
            value={cameraId}
            onChange={(event) => setCameraId(event.target.value ? Number(event.target.value) : "")}
          >
            <option value="">Selecione uma câmera</option>
            {cameras.data?.map((camera) => (
              <option value={camera.id} key={camera.id}>
                {camera.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Início
          <input type="datetime-local" value={start} onChange={(event) => setStart(event.target.value)} />
        </label>
        <label>
          Fim
          <input type="datetime-local" value={end} onChange={(event) => setEnd(event.target.value)} />
        </label>
      </section>
      {new Date(start) >= new Date(end) && (
        <div className="alert error">O início deve ser anterior ao fim.</div>
      )}
      {recordings.isError && <div className="alert error">{apiMessage(recordings.error)}</div>}
      <section className="recording-list">
        {recordings.data?.map((recording) => (
          <article key={recording.url}>
            <div>
              <strong>{new Date(recording.start).toLocaleString("pt-BR")}</strong>
              <small>{Math.round(recording.duration)} segundos</small>
            </div>
            <video controls preload="metadata" src={recording.url} />
            <a className="button ghost recording-download" href={recording.url} download>
              <Download size={16} /> Baixar MP4
            </a>
          </article>
        ))}
        {cameraId && recordings.isSuccess && !recordings.data?.length && (
          <div className="empty">Não há segmentos neste período.</div>
        )}
      </section>
    </>
  );
}
