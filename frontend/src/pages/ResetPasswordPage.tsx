import { KeyRound } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { authApi } from "../api/auth";
import { AuthShell } from "../components/AuthShell";
import { apiMessage } from "../hooks/useApiError";

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(token ? null : "Link de recuperação inválido.");
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (password !== confirmation) {
      setError("As senhas não são iguais.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setMessage((await authApi.resetPassword(token, password)).message);
    } catch (reason) {
      setError(apiMessage(reason));
    } finally {
      setBusy(false);
    }
  };
  return (
    <AuthShell>
      <div className="auth-card">
        <div className="auth-card-heading">
          <p className="eyebrow">Nova credencial</p>
          <h2>Definir nova senha</h2>
          <p>Use pelo menos 12 caracteres e não repita sua senha atual.</p>
        </div>
        {error && (
          <div className="auth-notice" role="alert">
            {error}
          </div>
        )}
        {message ? (
          <div className="auth-notice success" role="status">
            {message}
            <Link to="/login">Entrar agora</Link>
          </div>
        ) : (
          <form className="auth-form" onSubmit={(event) => void submit(event)}>
            <label>
              Nova senha
              <span className="auth-input">
                <KeyRound size={17} />
                <input
                  type="password"
                  autoComplete="new-password"
                  minLength={12}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </span>
            </label>
            <label>
              Confirmar senha
              <span className="auth-input">
                <KeyRound size={17} />
                <input
                  type="password"
                  autoComplete="new-password"
                  minLength={12}
                  value={confirmation}
                  onChange={(event) => setConfirmation(event.target.value)}
                  required
                />
              </span>
            </label>
            <button className="button primary auth-submit" disabled={busy || !token}>
              {busy ? "Salvando…" : "Salvar nova senha"}
            </button>
          </form>
        )}
      </div>
    </AuthShell>
  );
}
