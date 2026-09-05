import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit3, Plus, Search, Trash2 } from "lucide-react";
import { useMemo, useState, type FormEvent } from "react";
import { accessApi } from "../api/access";
import { useAuth } from "../auth/useAuth";
import { Modal } from "../components/Modal";
import { apiMessage } from "../hooks/useApiError";
import type { UserInput, UserRecord } from "../types/api";

const blank: UserInput = { full_name: "", email: "", password: "", is_active: true, role_ids: [] };

export function UsersPage() {
  const { can } = useAuth();
  const canAssignRoles = can("permissions.manage");
  const client = useQueryClient();
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<UserRecord | "new" | null>(null);
  const [form, setForm] = useState<UserInput>(blank);
  const [notice, setNotice] = useState<string | null>(null);
  const users = useQuery({ queryKey: ["users"], queryFn: accessApi.users });
  const roles = useQuery({ queryKey: ["roles"], queryFn: accessApi.roles, enabled: canAssignRoles });
  const save = useMutation({
    mutationFn: (input: UserInput) =>
      editing === "new"
        ? accessApi.createUser(input)
        : accessApi.updateUser((editing as UserRecord).id, input),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["users"] });
      setEditing(null);
    },
    onError: (error) => setNotice(apiMessage(error)),
  });
  const remove = useMutation({
    mutationFn: accessApi.removeUser,
    onSuccess: () => client.invalidateQueries({ queryKey: ["users"] }),
    onError: (error) => setNotice(apiMessage(error)),
  });
  const filtered = useMemo(
    () =>
      users.data?.filter((user) =>
        `${user.full_name} ${user.email}`.toLowerCase().includes(search.toLowerCase()),
      ) ?? [],
    [users.data, search],
  );
  const open = (user?: UserRecord) => {
    setEditing(user ?? "new");
    setForm(
      user
        ? {
            full_name: user.full_name,
            email: user.email,
            is_active: user.is_active,
            password: "",
            role_ids:
              roles.data?.filter((role) => user.roles.includes(role.name)).map((role) => role.id) ?? [],
          }
        : blank,
    );
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    const input: Partial<UserInput> = { ...form };
    if (!input.password) delete input.password;
    if (!canAssignRoles && editing !== "new") delete input.role_ids;
    save.mutate(input as UserInput);
  };
  const destroy = (user: UserRecord) => {
    if (window.confirm(`Excluir o usuário “${user.full_name}”?`)) remove.mutate(user.id);
  };

  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">Controle de acesso</p>
          <h1>Usuários</h1>
          <p>Operadores, clientes e administradores da central.</p>
        </div>
        <button className="button primary" onClick={() => open()}>
          <Plus size={17} />
          Criar usuário
        </button>
      </header>
      {notice && (
        <div className="alert error" role="alert">
          {notice}
        </div>
      )}
      <section className="toolbar">
        <label className="search">
          <Search size={17} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Nome ou e-mail"
            aria-label="Buscar usuários"
          />
        </label>
        <span>{filtered.length} usuários</span>
      </section>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Usuário</th>
              <th>Perfis</th>
              <th>Estado</th>
              <th>
                <span className="visually-hidden">Ações</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((user) => (
              <tr key={user.id}>
                <td>
                  <strong>{user.full_name}</strong>
                  <small>{user.email}</small>
                </td>
                <td>{user.roles.join(", ") || "Sem perfil"}</td>
                <td>
                  <span className={`status ${user.is_active ? "status-online" : "status-offline"}`}>
                    <i />
                    {user.is_active ? "Ativo" : "Inativo"}
                  </span>
                </td>
                <td className="actions">
                  <button
                    className="icon-button"
                    onClick={() => open(user)}
                    aria-label={`Editar ${user.full_name}`}
                  >
                    <Edit3 size={16} />
                  </button>
                  <button
                    className="icon-button danger"
                    onClick={() => destroy(user)}
                    aria-label={`Excluir ${user.full_name}`}
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editing && (
        <Modal
          title={editing === "new" ? "Criar usuário" : "Editar usuário"}
          onClose={() => setEditing(null)}
        >
          <form className="form-grid" onSubmit={submit}>
            <label className="field field-wide">
              Nome
              <input
                value={form.full_name}
                onChange={(event) => setForm({ ...form, full_name: event.target.value })}
                minLength={2}
                required
              />
            </label>
            <label className="field field-wide">
              E-mail
              <input
                type="email"
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
                required
              />
            </label>
            <label className="field field-wide">
              {editing === "new" ? "Senha" : "Nova senha (opcional)"}
              <input
                type="password"
                autoComplete="new-password"
                value={form.password}
                onChange={(event) => setForm({ ...form, password: event.target.value })}
                required={editing === "new"}
                minLength={12}
              />
            </label>
            <fieldset className="field field-wide check-list">
              <legend>Perfis</legend>
              {!canAssignRoles && (
                <p>Seu acesso permite editar usuários, mas não consultar ou alterar perfis.</p>
              )}
              {canAssignRoles &&
                roles.data?.map((role) => (
                  <label key={role.id}>
                    <input
                      type="checkbox"
                      checked={form.role_ids.includes(role.id)}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          role_ids: event.target.checked
                            ? [...form.role_ids, role.id]
                            : form.role_ids.filter((id) => id !== role.id),
                        })
                      }
                    />
                    {role.name}
                  </label>
                ))}
            </fieldset>
            <label className="toggle field-wide">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
              />
              Usuário ativo
            </label>
            <footer className="modal-actions">
              <button type="button" className="button ghost" onClick={() => setEditing(null)}>
                Cancelar
              </button>
              <button className="button primary" disabled={save.isPending}>
                {save.isPending ? "Salvando…" : "Salvar usuário"}
              </button>
            </footer>
          </form>
        </Modal>
      )}
    </>
  );
}
