import { ArrowLeft, MailCheck } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { authApi } from "../api/auth";
import { AuthShell } from "../components/AuthShell";
import { apiMessage } from "../hooks/useApiError";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setMessage((await authApi.forgotPassword(email)).message);
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
          <p className="eyebrow">Recuperação de acesso</p>
          <h2>Redefinir senha</h2>
          <p>Informe seu e-mail para receber as instruções de redefinição.</p>
        </div>
        {message ? (
          <div className="auth-notice success" role="status">
            <MailCheck size={18} />
            {message}
          </div>
        ) : (
          <form className="auth-form" onSubmit={(event) => void submit(event)}>
            {error && (
              <div className="auth-notice" role="alert">
                {error}
              </div>
            )}
            <label>
              E-mail corporativo
              <span className="auth-input">
                <MailCheck size={17} />
                <input
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </span>
            </label>
            <button className="button primary auth-submit" disabled={busy}>
              {busy ? "Enviando…" : "Solicitar redefinição"}
            </button>
          </form>
        )}
        <Link className="auth-back" to="/login">
          <ArrowLeft size={16} />
          Voltar para entrar
        </Link>
      </div>
    </AuthShell>
  );
}
