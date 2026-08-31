import { KeyRound, LockKeyhole, Mail } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { AuthShell } from "../components/AuthShell";

export function LoginPage() {
  const [message, setMessage] = useState<string | null>(null);

  return (
    <AuthShell>
      <div className="auth-card">
        <div className="auth-card-heading">
          <p className="eyebrow">IDENTIFICAÇÃO DO OPERADOR</p>
          <h2>Entrar na central</h2>
          <p>Informe suas credenciais corporativas para continuar.</p>
        </div>
        {message && <div className="auth-notice">{message}</div>}
        <form
          className="auth-form"
          onSubmit={(event) => {
            event.preventDefault();
            setMessage("A autenticação ainda não está disponível na API. Nenhum acesso foi efetuado.");
          }}
        >
          <label>
            E-mail corporativo
            <span className="auth-input">
              <Mail size={17} />
              <input type="email" autoComplete="email" required />
            </span>
          </label>
          <label>
            Senha
            <span className="auth-input">
              <LockKeyhole size={17} />
              <input type="password" autoComplete="current-password" required />
            </span>
          </label>
          <div className="auth-options">
            <label className="toggle">
              <input type="checkbox" /> Manter esta estação identificada
            </label>
            <Link to="/forgot-password">Recuperar acesso</Link>
          </div>
          <button className="button primary auth-submit">
            <KeyRound size={17} />
            Entrar
          </button>
        </form>
        <p className="auth-footnote">Integração de login pendente da API de autenticação.</p>
      </div>
    </AuthShell>
  );
}
