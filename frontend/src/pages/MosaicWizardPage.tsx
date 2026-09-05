import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, Check, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { accessApi } from "../api/access";
import { camerasApi } from "../api/cameras";
import { mosaicsApi } from "../api/mosaics";
import { useAuth } from "../auth/useAuth";
import { MosaicGlyph } from "../components/MosaicLayout";
import { apiMessage } from "../hooks/useApiError";
import type { MosaicInput } from "../types/api";

const steps = ["Dados básicos", "Usuários", "Câmeras"] as const;

export function MosaicWizardPage() {
  const { can } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const step = Math.min(3, Math.max(1, Number(params.get("step") || 1)));
  const [name, setName] = useState("");
  const [capacity, setCapacity] = useState(4);
  const [active, setActive] = useState(true);
  const [userIds, setUserIds] = useState<number[]>([]);
  const [roleIds, setRoleIds] = useState<number[]>([]);
  const [cameraIds, setCameraIds] = useState<number[]>([]);
  const [userSearch, setUserSearch] = useState("");
  const [cameraSearch, setCameraSearch] = useState("");
  const [dirty, setDirty] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const existing = useQuery({
    queryKey: ["mosaic", id],
    queryFn: () => mosaicsApi.get(Number(id)),
    enabled: Boolean(id),
  });
  const users = useQuery({ queryKey: ["users"], queryFn: accessApi.users, enabled: can("users.manage") });
  const roles = useQuery({
    queryKey: ["roles"],
    queryFn: accessApi.roles,
    enabled: can("permissions.manage"),
  });
  const cameras = useQuery({ queryKey: ["cameras"], queryFn: () => camerasApi.list(false) });

  useEffect(() => {
    if (!existing.data || initialized) return;
    setName(existing.data.name);
    setCapacity(existing.data.capacity);
    setActive(existing.data.active);
    setUserIds(existing.data.user_ids);
    setRoleIds(existing.data.role_ids);
    setCameraIds(
      [...existing.data.cameras].sort((a, b) => a.position - b.position).map((item) => item.camera_id),
    );
    setInitialized(true);
  }, [existing.data, initialized]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (!dirty) return;
      event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const filteredUsers = useMemo(
    () =>
      users.data?.filter((user) =>
        `${user.full_name} ${user.email}`.toLowerCase().includes(userSearch.toLowerCase()),
      ) ?? [],
    [users.data, userSearch],
  );
  const filteredCameras = useMemo(
    () =>
      cameras.data?.filter((camera) =>
        `${camera.name} ${camera.location}`.toLowerCase().includes(cameraSearch.toLowerCase()),
      ) ?? [],
    [cameras.data, cameraSearch],
  );
  const save = useMutation({
    mutationFn: (input: MosaicInput) =>
      id ? mosaicsApi.update(Number(id), input) : mosaicsApi.create(input),
    onSuccess: (mosaic) => {
      setDirty(false);
      navigate(`/mosaics/${mosaic.id}`);
    },
    onError: (error) => setNotice(apiMessage(error)),
  });
  const change = <T,>(setter: (value: T) => void, value: T) => {
    setter(value);
    setDirty(true);
  };
  const go = (next: number) => setParams({ step: String(next) });
  const validBasics = name.trim().length >= 2 && capacity >= 1 && capacity <= 36;
  const submit = () =>
    save.mutate({
      name: name.trim(),
      capacity,
      active,
      user_ids: userIds,
      role_ids: roleIds,
      cameras: cameraIds.map((camera_id, index) => ({ camera_id, position: index + 1 })),
    });
  const move = (index: number, direction: -1 | 1) => {
    const next = [...cameraIds];
    const target = index + direction;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    change(setCameraIds, next);
  };

  return (
    <>
      <header className="page-heading">
        <div>
          <Link className="back-link" to="/mosaics">
            <ArrowLeft size={16} />
            Mosaicos
          </Link>
          <h1>{id ? "Editar mosaico" : "Criar mosaico"}</h1>
          <p>Configure acesso e posição dos canais antes de salvar.</p>
        </div>
        <MosaicGlyph capacity={capacity} />
      </header>
      {notice && (
        <div className="alert error" role="alert">
          {notice}
        </div>
      )}
      <ol className="wizard-progress" aria-label="Etapas do cadastro">
        {steps.map((label, index) => (
          <li key={label} className={step === index + 1 ? "active" : step > index + 1 ? "complete" : ""}>
            <button onClick={() => go(index + 1)} disabled={index > 0 && !validBasics}>
              <span>{step > index + 1 ? <Check size={15} /> : index + 1}</span>
              {label}
            </button>
          </li>
        ))}
      </ol>
      <section className="wizard-panel">
        {step === 1 && (
          <div className="basic-grid">
            <label className="field">
              Nome do mosaico
              <input
                value={name}
                maxLength={120}
                onChange={(event) => change(setName, event.target.value)}
                required
              />
              <em>{name.length > 0 && name.trim().length < 2 ? "Informe ao menos 2 caracteres" : ""}</em>
            </label>
            <label className="field">
              Quantidade de posições
              <input
                type="number"
                min={1}
                max={36}
                value={capacity}
                onChange={(event) => {
                  const next = Math.min(36, Math.max(1, Number(event.target.value)));
                  setCapacity(next);
                  setCameraIds((current) => current.slice(0, next));
                  setDirty(true);
                }}
              />
              <span>Entre 1 e 36 posições.</span>
            </label>
            <label className="toggle">
              <input
                type="checkbox"
                checked={active}
                onChange={(event) => change(setActive, event.target.checked)}
              />
              Mosaico ativo
            </label>
          </div>
        )}
        {step === 2 && (
          <div className="selection-grid">
            <section>
              <h2>Usuários disponíveis</h2>
              {!can("users.manage") && (
                <div className="permission-note">
                  Sem permissão para pesquisar usuários. Os acessos existentes serão preservados.
                </div>
              )}
              <label className="search">
                <Search size={16} />
                <input
                  value={userSearch}
                  onChange={(event) => setUserSearch(event.target.value)}
                  placeholder="Nome ou e-mail…"
                  aria-label="Buscar usuários"
                />
              </label>
              <div className="pick-list">
                {filteredUsers.map((user) => (
                  <article key={user.id}>
                    <div>
                      <strong>{user.full_name}</strong>
                      <small>{user.email}</small>
                    </div>
                    <button
                      className="icon-button"
                      disabled={userIds.includes(user.id)}
                      onClick={() => change(setUserIds, [...userIds, user.id])}
                      aria-label={`Adicionar ${user.full_name}`}
                    >
                      <Plus size={18} />
                    </button>
                  </article>
                ))}
              </div>
              <h3>Perfis completos</h3>
              {!can("permissions.manage") && (
                <div className="permission-note">Sem permissão para pesquisar perfis.</div>
              )}
              <div className="check-list">
                {roles.data?.map((role) => (
                  <label key={role.id}>
                    <input
                      type="checkbox"
                      checked={roleIds.includes(role.id)}
                      onChange={(event) =>
                        change(
                          setRoleIds,
                          event.target.checked
                            ? [...roleIds, role.id]
                            : roleIds.filter((value) => value !== role.id),
                        )
                      }
                    />
                    {role.name}
                  </label>
                ))}
              </div>
            </section>
            <section>
              <h2>Usuários selecionados</h2>
              <div className="pick-list selected">
                {userIds.map((value) => {
                  const user = users.data?.find((item) => item.id === value);
                  return (
                    <article key={value}>
                      <div>
                        <strong>{user?.full_name ?? `Usuário #${value}`}</strong>
                        <small>{user?.email}</small>
                      </div>
                      <button
                        className="icon-button danger"
                        onClick={() =>
                          change(
                            setUserIds,
                            userIds.filter((item) => item !== value),
                          )
                        }
                        aria-label={`Remover ${user?.full_name ?? "usuário"}`}
                      >
                        <Trash2 size={16} />
                      </button>
                    </article>
                  );
                })}
                {!userIds.length && !roleIds.length && (
                  <div className="empty">Nenhum acesso selecionado.</div>
                )}
              </div>
            </section>
          </div>
        )}
        {step === 3 && (
          <div className="selection-grid">
            <section>
              <h2>Câmeras disponíveis</h2>
              <label className="search">
                <Search size={16} />
                <input
                  value={cameraSearch}
                  onChange={(event) => setCameraSearch(event.target.value)}
                  placeholder="Nome ou localização…"
                  aria-label="Buscar câmeras"
                />
              </label>
              <div className="pick-list">
                {filteredCameras.map((camera) => (
                  <article key={camera.id}>
                    <div>
                      <strong>{camera.name}</strong>
                      <small>{camera.location || "Local não informado"}</small>
                    </div>
                    <button
                      className="icon-button"
                      disabled={cameraIds.includes(camera.id) || cameraIds.length >= capacity}
                      onClick={() => change(setCameraIds, [...cameraIds, camera.id])}
                      aria-label={`Adicionar ${camera.name}`}
                    >
                      <Plus size={18} />
                    </button>
                  </article>
                ))}
              </div>
            </section>
            <section>
              <h2>
                Posições{" "}
                <span>
                  {cameraIds.length}/{capacity}
                </span>
              </h2>
              <div className="pick-list selected">
                {cameraIds.map((value, index) => {
                  const camera = cameras.data?.find((item) => item.id === value);
                  return (
                    <article key={value}>
                      <b>{index + 1}</b>
                      <div>
                        <strong>{camera?.name ?? `Câmera #${value}`}</strong>
                        <small>{camera?.location}</small>
                      </div>
                      <button
                        className="icon-button"
                        disabled={index === 0}
                        onClick={() => move(index, -1)}
                        aria-label="Mover para cima"
                      >
                        <ArrowUp size={15} />
                      </button>
                      <button
                        className="icon-button"
                        disabled={index === cameraIds.length - 1}
                        onClick={() => move(index, 1)}
                        aria-label="Mover para baixo"
                      >
                        <ArrowDown size={15} />
                      </button>
                      <button
                        className="icon-button danger"
                        onClick={() =>
                          change(
                            setCameraIds,
                            cameraIds.filter((item) => item !== value),
                          )
                        }
                        aria-label={`Remover ${camera?.name}`}
                      >
                        <Trash2 size={16} />
                      </button>
                    </article>
                  );
                })}
                {!cameraIds.length && <div className="empty">Adicione ao menos uma câmera.</div>}
              </div>
            </section>
          </div>
        )}
      </section>
      <footer className="wizard-actions">
        <Link className="button ghost" to="/mosaics">
          Cancelar
        </Link>
        <div>
          {step > 1 && (
            <button className="button" onClick={() => go(step - 1)}>
              <ArrowLeft size={16} />
              Voltar
            </button>
          )}
          {step < 3 ? (
            <button className="button primary" disabled={!validBasics} onClick={() => go(step + 1)}>
              Avançar
              <ArrowRight size={16} />
            </button>
          ) : (
            <button
              className="button primary"
              disabled={!cameraIds.length || save.isPending}
              onClick={submit}
            >
              {save.isPending ? "Salvando…" : id ? "Salvar alterações" : "Criar mosaico"}
            </button>
          )}
        </div>
      </footer>
    </>
  );
}
