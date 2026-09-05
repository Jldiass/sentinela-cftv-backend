import { useQuery } from "@tanstack/react-query";
import { systemApi } from "../api/system";
import { ServiceStatus } from "../components/Status";
import { apiMessage } from "../hooks/useApiError";
export function HealthPage() {
  const health = useQuery({ queryKey: ["health"], queryFn: systemApi.health, refetchInterval: 15_000 });
  if (health.isError)
    return (
      <>
        <header className="page-heading">
          <div>
            <p className="eyebrow">INFRAESTRUTURA</p>
            <h1>Saúde do sistema</h1>
          </div>
        </header>
        <div className="alert error">{apiMessage(health.error)}</div>
      </>
    );
  const data = health.data;
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INFRAESTRUTURA</p>
          <h1>Saúde do sistema</h1>
          <p>Atualização automática a cada 15 segundos.</p>
        </div>
        <ServiceStatus up={data?.ok ?? false} />
      </header>
      <section className="health-grid">
        <article>
          <small>API E BANCO DE DADOS</small>
          <strong>Banco de dados</strong>
          <ServiceStatus up={data?.database === "up"} />
        </article>
        <article>
          <small>SERVIÇO DE MÍDIA</small>
          <strong>MediaMTX</strong>
          <ServiceStatus up={data?.mediamtx === "up"} />
        </article>
        <article>
          <small>CANAIS EM TRANSMISSÃO</small>
          <strong>{data?.active_streams ?? "--"}</strong>
          <span>streams ativos</span>
        </article>
        <article>
          <small>RETENÇÃO EFETIVA</small>
          <strong>{data?.effective_retention_hours ?? "--"}h</strong>
          <span>janela móvel global</span>
        </article>
      </section>
      {data?.mediamtx === "down" && (
        <div className="alert error">
          O MediaMTX está indisponível. Os players e o playback podem não funcionar.
        </div>
      )}
    </>
  );
}
