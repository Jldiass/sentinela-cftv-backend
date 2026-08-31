import { Copy, KeyRound, RotateCw } from "lucide-react";
import { useState } from "react";
import type { StreamCredentials } from "../types/api";
export function Credentials({
  credentials,
  onRotate,
  rotating,
}: {
  credentials: StreamCredentials;
  onRotate: () => void;
  rotating: boolean;
}) {
  const [copied, setCopied] = useState<"url" | "server" | "key" | null>(null);
  const copy = async (kind: "url" | "server" | "key", value: string) => {
    await navigator.clipboard.writeText(value);
    setCopied(kind);
    setTimeout(() => setCopied(null), 1800);
  };
  return (
    <div className="credentials">
      <p>
        <KeyRound size={16} />
        No Mibo Smart ou Mibo Cam, apague o conteúdo antigo e cole somente a URL completa abaixo.
      </p>
      <div className="credential-group">
        <strong>URL para Mibo — campo “URL RTMP”</strong>
        <div className="credential-value">
          <code>{credentials.rtmp_url}</code>
          <button
            className="icon-button"
            onClick={() => copy("url", credentials.rtmp_url)}
            title="Copiar URL RTMP completa"
          >
            <Copy size={17} />
          </button>
        </div>
        {copied === "url" && <span className="copy-state">URL completa copiada</span>}
      </div>
      <details className="credential-advanced">
        <summary>Outro equipamento com campos separados</summary>
        <div className="credential-group">
          <label>Servidor RTMP</label>
          <div className="credential-value">
            <code>{credentials.rtmp_server_url}</code>
            <button
              className="icon-button"
              onClick={() => copy("server", credentials.rtmp_server_url)}
              title="Copiar servidor RTMP"
            >
              <Copy size={17} />
            </button>
          </div>
          <label>Chave do stream</label>
          <div className="credential-value">
            <code>{credentials.stream_key}</code>
            <button
              className="icon-button"
              onClick={() => copy("key", credentials.stream_key)}
              title="Copiar chave do stream"
            >
              <Copy size={17} />
            </button>
          </div>
          {(copied === "server" || copied === "key") && (
            <span className="copy-state">{copied === "server" ? "Servidor copiado" : "Chave copiada"}</span>
          )}
        </div>
      </details>
      <p className="credential-warning">
        No Mibo, use a URL completa uma única vez. Não acrescente outra chave ou endereço ao final.
      </p>
      <div className="modal-actions">
        <button className="button warning" onClick={onRotate} disabled={rotating}>
          <RotateCw size={16} />
          {rotating ? "Trocando..." : "Trocar chave"}
        </button>
      </div>
    </div>
  );
}
