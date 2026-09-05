import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, Eye, Play, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { camerasApi } from "../api/cameras";
import { eventsApi } from "../api/events";
import { useAuth } from "../auth/useAuth";
import { Modal } from "../components/Modal";
import { apiMessage } from "../hooks/useApiError";
import type { AlarmEvent, ClipStatus } from "../types/api";
export function EventsPage() {
  const { can } = useAuth();
  const client = useQueryClient();
  const [cameraId, setCameraId] = useState<number | "">("");
  const [creating, setCreating] = useState(false);
  const [kind, setKind] = useState("alarm");
  const [note, setNote] = useState("");
  const [happenedAt, setHappenedAt] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | ClipStatus>("all");
  const [details, setDetails] = useState<AlarmEvent | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const cameras = useQuery({ queryKey: ["cameras"], queryFn: () => camerasApi.list(false) });
  const events = useQuery({
    queryKey: ["events", cameraId],
    queryFn: () => eventsApi.list(cameraId || undefined),
    refetchInterval: 10_000,
  });
  const create = useMutation({
    mutationFn: () =>
      eventsApi.create(Number(cameraId), {
        kind,
        note,
        ...(happenedAt ? { happened_at: new Date(happenedAt).toISOString() } : {}),
      }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["events"] });
      setCreating(false);
      setKind("alarm");
      setNote("");
      setHappenedAt("");
    },
    onError: (error) => setNotice(`Registro de evento: ${apiMessage(error)}`),
  });
  const remove = useMutation({
    mutationFn: eventsApi.remove,
    onSuccess: () => client.invalidateQueries({ queryKey: ["events"] }),
    onError: (error) => setNotice(`Remoção do evento: ${apiMessage(error)}`),
  });
  const showDetails = async (id: number) => {
    try {
      setDetails(await eventsApi.get(id));
    } catch (error) {
      setNotice(`Detalhes do evento: ${apiMessage(error)}`);
    }
  };
  const filteredEvents = events.data?.filter(
    (event) => statusFilter === "all" || event.clip_status === statusFilter,
  );
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">OCORRÊNCIAS</p>
          <h1>Eventos</h1>
          <p>Clipes preservam o pré e o pós-alarme configurados na câmera.</p>
        </div>
        {can("events.manage") && (
          <button className="button primary" onClick={() => setCreating(true)} disabled={!cameraId}>
            <Plus size={17} />
            Registrar evento
          </button>
        )}
      </header>
      {notice && (
        <div className="alert error" role="alert">
          {notice}
          <button onClick={() => setNotice(null)} aria-label="Fechar aviso">
            ×
          </button>
        </div>
      )}
      <section className="toolbar">
        <label className="select-inline">
          Filtrar câmera
          <select
            value={cameraId}
            onChange={(event) => setCameraId(event.target.value ? Number(event.target.value) : "")}
          >
            <option value="">Todas as câmeras</option>
            {cameras.data?.map((camera) => (
              <option value={camera.id} key={camera.id}>
                {camera.name}
              </option>
            ))}
          </select>
        </label>
        <label className="select-inline">
          Estado do clipe
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as "all" | ClipStatus)}
          >
            <option value="all">Todos</option>
            <option value="pending">Finalizando</option>
            <option value="available">Disponível</option>
            <option value="expired">Expirado</option>
          </select>
        </label>
      </section>
      <section className="event-list">
        {filteredEvents?.map((event) => (
          <article key={event.id}>
            <div className={`event-mark event-${event.clip_status}`}>
              <BellRing size={18} />
            </div>
            <div className="event-body">
              <strong>{event.kind}</strong>
              <p>{event.note || "Sem observação"}</p>
              <small>
                {new Date(event.happened_at).toLocaleString("pt-BR")} · Câmera #{event.camera_id}
              </small>
            </div>
            <div className="event-state">
              <button
                className="icon-button"
                onClick={() => showDetails(event.id)}
                aria-label={`Ver detalhes do evento ${event.kind}`}
              >
                <Eye size={16} aria-hidden="true" />
              </button>
              <span className={`clip clip-${event.clip_status}`}>
                {event.clip_status === "pending"
                  ? "Finalizando clipe"
                  : event.clip_status === "available"
                    ? "Disponível"
                    : "Vídeo expirado"}
              </span>
              {event.playback_url && (
                <a
                  className="icon-button"
                  href={event.playback_url}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={`Reproduzir evento ${event.kind}`}
                >
                  <Play size={16} />
                </a>
              )}
              {can("events.manage") && (
                <button
                  className="icon-button danger"
                  onClick={() => {
                    if (window.confirm(`Remover o evento “${event.kind}”?`)) remove.mutate(event.id);
                  }}
                  aria-label={`Remover evento ${event.kind}`}
                >
                  <Trash2 size={16} />
                </button>
              )}
            </div>
          </article>
        ))}
        {events.isSuccess && !filteredEvents?.length && (
          <div className="empty">Nenhum evento encontrado.</div>
        )}
      </section>
      {creating && (
        <Modal title="Registrar evento" onClose={() => setCreating(false)}>
          <div className="form-grid">
            <label className="field field-wide">
              Câmera
              <select value={cameraId} onChange={(event) => setCameraId(Number(event.target.value))}>
                {cameras.data?.map((camera) => (
                  <option value={camera.id} key={camera.id}>
                    {camera.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field field-wide">
              Tipo
              <input value={kind} maxLength={60} onChange={(event) => setKind(event.target.value)} />
            </label>
            <label className="field field-wide">
              Observação
              <textarea value={note} maxLength={500} onChange={(event) => setNote(event.target.value)} />
            </label>
            <label className="field field-wide">
              Data e hora da ocorrência <span>(opcional; padrão: agora)</span>
              <input
                type="datetime-local"
                value={happenedAt}
                max={new Date().toISOString().slice(0, 16)}
                onChange={(event) => setHappenedAt(event.target.value)}
              />
            </label>
            <footer className="modal-actions">
              <button className="button ghost" onClick={() => setCreating(false)}>
                Cancelar
              </button>
              <button className="button primary" onClick={() => create.mutate()} disabled={create.isPending}>
                {create.isPending ? "Registrando…" : "Registrar"}
              </button>
            </footer>
          </div>
        </Modal>
      )}
      {details && (
        <Modal title="Detalhes do evento" onClose={() => setDetails(null)}>
          <div className="details-panel">
            <div className="details-title">
              <div>
                <p className="eyebrow">EVENTO #{details.id}</p>
                <h3>{details.kind}</h3>
              </div>
              <span className={`clip clip-${details.clip_status}`}>{details.clip_status}</span>
            </div>
            <dl className="detail-grid">
              <div>
                <dt>CÂMERA</dt>
                <dd>#{details.camera_id}</dd>
              </div>
              <div>
                <dt>OCORRÊNCIA</dt>
                <dd>{new Date(details.happened_at).toLocaleString("pt-BR")}</dd>
              </div>
              <div>
                <dt>INÍCIO DO CLIPE</dt>
                <dd>{new Date(details.clip_start).toLocaleString("pt-BR")}</dd>
              </div>
              <div>
                <dt>DURAÇÃO</dt>
                <dd>{details.clip_duration} segundos</dd>
              </div>
            </dl>
            <p className="detail-note">{details.note || "Sem observação registrada."}</p>
            {details.playback_url ? (
              <video className="event-player" controls src={details.playback_url} />
            ) : (
              <div className="alert error">
                {details.clip_status === "pending"
                  ? "Finalizando clipe; esta tela atualiza automaticamente."
                  : "O vídeo deste evento expirou."}
              </div>
            )}
          </div>
        </Modal>
      )}
    </>
  );
}
