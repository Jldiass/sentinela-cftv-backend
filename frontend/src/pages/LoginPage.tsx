import { KeyRound, LockKeyhole, Mail } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { homeFor, useAuth } from "../auth/useAuth";
import { AuthShell } from "../components/AuthShell";
import { apiMessage } from "../hooks/useApiError";
export function LoginPage() {
  const { user, ready, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  if (ready && user) return <Navigate to={homeFor(user)} replace />;
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      const currentUser = await login(email, password);
      const from = (location.state as { from?: string } | null)?.from;
      navigate(from || homeFor(currentUser), { replace: true });
    } catch (error) {
      setMessage(apiMessage(error));
    } finally {
      setBusy(false);
    }
  };
  return (
    <AuthShell>
      <div className="auth-card">
        <div className="auth-card-heading">
          <p className="eyebrow">Identificação do operador</p>
          <h2>Entrar na central</h2>
          <p>Use suas credenciais para acessar os canais autorizados.</p>
        </div>
        {message && (
          <div className="auth-notice" role="alert">
            {message}
          </div>
        )}
        <form className="auth-form" onSubmit={(event) => void submit(event)}>
          <label>
            E-mail corporativo
            <span className="auth-input">
              <Mail size={17} aria-hidden="true" />
              <input
                name="email"
                type="email"
                autoComplete="email"
                spellCheck={false}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </span>
          </label>
          <label>
            Senha
            <span className="auth-input">
              <LockKeyhole size={17} aria-hidden="true" />
              <input
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </span>
          </label>
          <div className="auth-options">
            <Link to="/register">Primeiro acesso</Link>
            <Link to="/forgot-password">Esqueci minha senha</Link>
          </div>
          <button className="button primary auth-submit" disabled={busy}>
            <KeyRound size={17} aria-hidden="true" />
            {busy ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </div>
    </AuthShell>
  );
}
