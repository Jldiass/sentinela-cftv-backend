import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit3, Eye, Plus, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { mosaicsApi } from "../api/mosaics";
import { useAuth } from "../auth/useAuth";
import { MosaicGlyph } from "../components/MosaicLayout";
import { apiMessage } from "../hooks/useApiError";
export function MosaicsPage() {
  const { can } = useAuth();
  const client = useQueryClient();
  const [search, setSearch] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const canManage = can("mosaics.manage");
  const mosaics = useQuery({
    queryKey: ["mosaics", search, canManage],
    queryFn: () => mosaicsApi.list(search, canManage),
  });
  const remove = useMutation({
    mutationFn: mosaicsApi.remove,
    onSuccess: () => client.invalidateQueries({ queryKey: ["mosaics"] }),
    onError: (e) => setNotice(apiMessage(e)),
  });
  const destroy = (id: number, name: string) => {
    if (window.confirm(`Excluir o mosaico “${name}”?`)) remove.mutate(id);
  };
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">Postos de vídeo</p>
          <h1>Mosaicos</h1>
          <p>Grades salvas para cada rotina de monitoramento.</p>
        </div>
        {can("mosaics.manage") && (
          <Link className="button primary" to="/mosaics/new">
            <Plus size={17} aria-hidden="true" />
            Criar mosaico
          </Link>
        )}
      </header>
      {notice && (
        <div className="alert error" role="alert">
          {notice}
          <button aria-label="Fechar aviso" onClick={() => setNotice(null)}>
            ×
          </button>
        </div>
      )}
      <section className="toolbar">
        <label className="search">
          <Search size={17} aria-hidden="true" />
          <span className="visually-hidden">Buscar mosaicos</span>
          <input
            name="search"
            autoComplete="off"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Ex.: Portaria…"
          />
        </label>
        <span>{mosaics.data?.length ?? 0} mosaicos</span>
      </section>
      {mosaics.isError ? (
        <div className="alert error" role="alert">
          {apiMessage(mosaics.error)}
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Layout</th>
                <th>Nome</th>
                <th>Capacidade</th>
                <th>Câmeras</th>
                <th>Usuários</th>
                <th>Estado</th>
                <th>
                  <span className="visually-hidden">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {mosaics.data?.map((m) => (
                <tr key={m.id}>
                  <td>
                    <MosaicGlyph capacity={m.capacity} />
                  </td>
                  <td>
                    <strong>{m.name}</strong>
                  </td>
                  <td className="numeric">{m.capacity}</td>
                  <td className="numeric">{m.camera_count}</td>
                  <td className="numeric">{m.user_count}</td>
                  <td>
                    <span className={`status ${m.active ? "status-online" : "status-offline"}`}>
                      <i />
                      {m.active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td className="actions">
                    <Link className="icon-button" to={`/mosaics/${m.id}`} aria-label={`Visualizar ${m.name}`}>
                      <Eye size={16} aria-hidden="true" />
                    </Link>
                    {can("mosaics.manage") && (
                      <>
                        <Link
                          className="icon-button"
                          to={`/mosaics/${m.id}/edit`}
                          aria-label={`Editar ${m.name}`}
                        >
                          <Edit3 size={16} aria-hidden="true" />
                        </Link>
                        <button
                          className="icon-button danger"
                          onClick={() => destroy(m.id, m.name)}
                          aria-label={`Excluir ${m.name}`}
                        >
                          <Trash2 size={16} aria-hidden="true" />
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {mosaics.isSuccess && !mosaics.data.length && (
                <tr>
                  <td colSpan={7} className="empty">
                    Nenhum mosaico encontrado. Crie uma grade para iniciar o monitoramento.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
