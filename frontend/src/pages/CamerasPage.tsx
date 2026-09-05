import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit3, Eye, KeyRound, Plus, Search, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { camerasApi } from "../api/cameras";
import { useAuth } from "../auth/useAuth";
import { CameraForm } from "../components/CameraForm";
import { CameraDetails } from "../components/CameraDetails";
import { Credentials } from "../components/Credentials";
import { Modal } from "../components/Modal";
import { CameraStatusBadge } from "../components/Status";
import { apiMessage } from "../hooks/useApiError";
import type { Camera, CameraInput, CameraUpdate, StreamCredentials } from "../types/api";
export function CamerasPage() {
  const { can } = useAuth();
  const client = useQueryClient();
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Camera | null | "new">(null);
  const [credentials, setCredentials] = useState<StreamCredentials | null>(null);
  const [details, setDetails] = useState<Camera | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const cameras = useQuery({
    queryKey: ["cameras"],
    queryFn: () => camerasApi.list(true),
    refetchInterval: 12_000,
  });
  const refresh = () => client.invalidateQueries({ queryKey: ["cameras"] });
  const save = useMutation({
    mutationFn: (input: CameraInput | CameraUpdate) =>
      editing === "new"
        ? camerasApi.create(input as CameraInput)
        : camerasApi.update((editing as Camera).id, input as CameraUpdate),
    onSuccess: async (camera) => {
      refresh();
      setEditing(null);
      if (editing === "new") {
        try {
          setCredentials(await camerasApi.stream(camera.id));
        } catch (error) {
          setNotice(`Câmera cadastrada, mas as credenciais não puderam ser abertas: ${apiMessage(error)}`);
        }
      }
    },
    onError: (error) =>
      setNotice(`${editing === "new" ? "Cadastro" : "Atualização"} da câmera: ${apiMessage(error)}`),
  });
  const remove = useMutation({
    mutationFn: camerasApi.remove,
    onSuccess: refresh,
    onError: (error) => setNotice(`Exclusão bloqueada: ${apiMessage(error)}`),
  });
  const rotate = useMutation({
    mutationFn: camerasApi.rotateKey,
    onSuccess: (stream) => {
      setCredentials(stream);
      refresh();
    },
    onError: (error) => setNotice(`Troca de chave bloqueada: ${apiMessage(error)}`),
  });
  const filtered = useMemo(
    () =>
      cameras.data?.filter((camera) =>
        `${camera.name} ${camera.location}`.toLowerCase().includes(search.toLowerCase()),
      ) ?? [],
    [cameras.data, search],
  );
  const showCredentials = async (id: number) => {
    try {
      setCredentials(await camerasApi.stream(id));
    } catch (error) {
      setNotice(apiMessage(error));
    }
  };
  const showDetails = async (id: number) => {
    try {
      setDetails(await camerasApi.get(id));
    } catch (error) {
      setNotice(`Detalhes da câmera: ${apiMessage(error)}`);
    }
  };
  const deleteCamera = (camera: Camera) => {
    if (
      window.confirm(
        `Excluir o cadastro de “${camera.name}”? Esta ação remove também os eventos relacionados.`,
      )
    )
      remove.mutate(camera.id);
  };
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">CONFIGURAÇÃO</p>
          <h1>Câmeras</h1>
          <p>Até oito cadastros. URLs de publicação são geradas pelo servidor.</p>
        </div>
        {can("cameras.manage") && (
          <button className="button primary" onClick={() => setEditing("new")}>
            <Plus size={17} />
            Nova câmera
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
        <label className="search">
          <Search size={17} aria-hidden="true" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Nome ou localização…"
            aria-label="Buscar câmeras"
          />
        </label>
        <span>
          {filtered.length} de {cameras.data?.length ?? 0} câmeras
        </span>
      </section>
      {cameras.isError ? (
        <div className="alert error">{apiMessage(cameras.error)}</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Câmera</th>
                <th>Estado</th>
                <th>Áudio</th>
                <th>Alarmes</th>
                <th>Publicação</th>
                <th aria-label="Ações" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((camera) => (
                <tr key={camera.id} className={!camera.enabled ? "muted-row" : ""}>
                  <td>
                    <strong>{camera.name}</strong>
                    <small>
                      {camera.location || "Local não informado"}
                      {!camera.enabled && " · Desabilitada"}
                    </small>
                  </td>
                  <td>
                    <CameraStatusBadge status={camera.status} />
                  </td>
                  <td>{camera.audio_enabled ? "Habilitado" : "Desativado"}</td>
                  <td>
                    {camera.pre_alarm_seconds}s antes · {camera.post_alarm_seconds}s depois
                  </td>
                  <td>
                    {can("cameras.manage") ? (
                      <button className="text-button" onClick={() => showCredentials(camera.id)}>
                        <KeyRound size={15} />
                        RTMP
                      </button>
                    ) : (
                      "Restrita"
                    )}
                  </td>
                  <td className="actions">
                    <button
                      className="icon-button"
                      aria-label={`Ver detalhes de ${camera.name}`}
                      onClick={() => showDetails(camera.id)}
                    >
                      <Eye size={16} aria-hidden="true" />
                    </button>
                    {can("cameras.manage") && (
                      <button
                        className="icon-button"
                        aria-label={`Editar ${camera.name}`}
                        onClick={() => setEditing(camera)}
                      >
                        <Edit3 size={16} aria-hidden="true" />
                      </button>
                    )}
                    {can("cameras.manage") && (
                      <button
                        className="icon-button danger"
                        aria-label={`Excluir ${camera.name}`}
                        onClick={() => deleteCamera(camera)}
                      >
                        <Trash2 size={16} aria-hidden="true" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {!filtered.length && (
                <tr>
                  <td colSpan={6} className="empty">
                    Nenhuma câmera encontrada.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {editing && (
        <Modal
          title={editing === "new" ? "Cadastrar câmera" : "Editar câmera"}
          onClose={() => setEditing(null)}
        >
          <CameraForm
            camera={editing === "new" ? undefined : editing}
            onSubmit={(values) => save.mutate(values)}
            busy={save.isPending}
            onCancel={() => setEditing(null)}
          />
        </Modal>
      )}
      {credentials && (
        <Modal title="Credenciais de publicação" onClose={() => setCredentials(null)}>
          <Credentials
            credentials={credentials}
            onRotate={() => rotate.mutate(credentials.camera_id)}
            rotating={rotate.isPending}
          />
        </Modal>
      )}
      {details && (
        <Modal title="Detalhes da câmera" onClose={() => setDetails(null)}>
          <CameraDetails camera={details} />
        </Modal>
      )}
    </>
  );
}
