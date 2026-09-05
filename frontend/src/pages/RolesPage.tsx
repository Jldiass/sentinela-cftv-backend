import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit3, Plus, Trash2 } from "lucide-react";
import { useMemo, useState, type FormEvent } from "react";
import { accessApi } from "../api/access";
import { Modal } from "../components/Modal";
import { apiMessage } from "../hooks/useApiError";
import type { Permission, Role, RoleInput } from "../types/api";

const blank: RoleInput = { name: "", description: "", permission_codes: [] };
const groupName = (code: string) =>
  ({
    overview: "Visão geral",
    mosaics: "Mosaicos",
    cameras: "Câmeras",
    events: "Eventos",
    reports: "Relatórios",
    users: "Usuários",
    permissions: "Permissões",
    system: "Sistema",
  })[code.split(".")[0]] ?? "Outras";

export function RolesPage() {
  const client = useQueryClient();
  const [editing, setEditing] = useState<Role | "new" | null>(null);
  const [form, setForm] = useState<RoleInput>(blank);
  const [notice, setNotice] = useState<string | null>(null);
  const roles = useQuery({ queryKey: ["roles"], queryFn: accessApi.roles });
  const permissions = useQuery({ queryKey: ["permissions"], queryFn: accessApi.permissions });
  const grouped = useMemo(
    () =>
      (permissions.data ?? []).reduce<Record<string, Permission[]>>((result, permission) => {
        const group = groupName(permission.code);
        (result[group] ??= []).push(permission);
        return result;
      }, {}),
    [permissions.data],
  );
  const save = useMutation({
    mutationFn: (input: RoleInput) =>
      editing === "new" ? accessApi.createRole(input) : accessApi.updateRole((editing as Role).id, input),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["roles"] });
      setEditing(null);
    },
    onError: (error) => setNotice(apiMessage(error)),
  });
  const remove = useMutation({
    mutationFn: accessApi.removeRole,
    onSuccess: () => client.invalidateQueries({ queryKey: ["roles"] }),
    onError: (error) => setNotice(apiMessage(error)),
  });
  const open = (role?: Role) => {
    setEditing(role ?? "new");
    setForm(
      role
        ? { name: role.name, description: role.description, permission_codes: role.permission_codes }
        : blank,
    );
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    save.mutate(form);
  };

  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">Política operacional</p>
          <h1>Perfis e permissões</h1>
          <p>Defina o que cada função pode consultar ou administrar.</p>
        </div>
        <button className="button primary" onClick={() => open()}>
          <Plus size={17} />
          Criar perfil
        </button>
      </header>
      {notice && (
        <div className="alert error" role="alert">
          {notice}
        </div>
      )}
      <div className="role-grid">
        {roles.data?.map((role) => (
          <article key={role.id}>
            <header>
              <div>
                <h2>{role.name}</h2>
                <p>{role.description}</p>
              </div>
              <span>{role.user_count} usuários</span>
            </header>
            <div className="permission-chips">
              {role.permission_codes.map((code) => (
                <span key={code}>{code}</span>
              ))}
            </div>
            <footer>
              <button className="button ghost" onClick={() => open(role)}>
                <Edit3 size={16} />
                Editar perfil
              </button>
              {!role.is_system && (
                <button
                  className="icon-button danger"
                  aria-label={`Excluir ${role.name}`}
                  onClick={() => {
                    if (window.confirm(`Excluir o perfil “${role.name}”?`)) remove.mutate(role.id);
                  }}
                >
                  <Trash2 size={16} />
                </button>
              )}
            </footer>
          </article>
        ))}
      </div>
      {editing && (
        <Modal title={editing === "new" ? "Criar perfil" : "Editar perfil"} onClose={() => setEditing(null)}>
          <form className="form-grid role-form" onSubmit={submit}>
            <label className="field field-wide">
              Nome
              <input
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                disabled={editing !== "new" && editing.is_system}
                minLength={2}
                required
              />
            </label>
            <label className="field field-wide">
              Descrição
              <textarea
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
              />
            </label>
            {Object.entries(grouped).map(([group, items]) => (
              <fieldset className="field field-wide check-list" key={group}>
                <legend>{group}</legend>
                {items.map((permission) => (
                  <label key={permission.code}>
                    <input
                      type="checkbox"
                      checked={form.permission_codes.includes(permission.code)}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          permission_codes: event.target.checked
                            ? [...form.permission_codes, permission.code]
                            : form.permission_codes.filter((code) => code !== permission.code),
                        })
                      }
                    />
                    <span>
                      <strong>{permission.code}</strong>
                      <small>{permission.description}</small>
                    </span>
                  </label>
                ))}
              </fieldset>
            ))}
            <footer className="modal-actions">
              <button type="button" className="button ghost" onClick={() => setEditing(null)}>
                Cancelar
              </button>
              <button className="button primary" disabled={save.isPending}>
                {save.isPending ? "Salvando…" : "Salvar perfil"}
              </button>
            </footer>
          </form>
        </Modal>
      )}
    </>
  );
}
