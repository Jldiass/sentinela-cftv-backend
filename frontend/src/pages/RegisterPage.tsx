import { ShieldCheck } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { homeFor, useAuth } from "../auth/useAuth";
import { AuthShell } from "../components/AuthShell";
import { apiMessage } from "../hooks/useApiError";

export function RegisterPage() {
  const { user, ready, register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (ready && user) return <Navigate to={homeFor(user)} replace />;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (password !== confirmation) {
      setError("As senhas não são iguais.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await register(email, fullName, password);
      navigate("/", { replace: true });
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
          <p className="eyebrow">Configuração inicial</p>
          <h2>Criar administrador</h2>
          <p>Disponível somente enquanto a central ainda não possui usuários.</p>
        </div>
        {error && (
          <div className="auth-notice" role="alert">
            {error}
          </div>
        )}
        <form className="auth-form" onSubmit={(event) => void submit(event)}>
          <label>
            Nome completo
            <span className="auth-input">
              <input
                autoComplete="name"
                minLength={2}
                maxLength={120}
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                required
              />
            </span>
          </label>
          <label>
            E-mail
            <span className="auth-input">
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </span>
          </label>
          <label>
            Senha
            <span className="auth-input">
              <input
                type="password"
                autoComplete="new-password"
                minLength={12}
                maxLength={128}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </span>
          </label>
          <label>
            Confirmar senha
            <span className="auth-input">
              <input
                type="password"
                autoComplete="new-password"
                minLength={12}
                maxLength={128}
                value={confirmation}
                onChange={(event) => setConfirmation(event.target.value)}
                required
              />
            </span>
          </label>
          <button className="button primary auth-submit" disabled={busy}>
            <ShieldCheck size={17} aria-hidden="true" />
            {busy ? "Criando…" : "Criar administrador"}
          </button>
        </form>
        <Link className="auth-back" to="/login">
          Voltar para entrar
        </Link>
      </div>
    </AuthShell>
  );
}
