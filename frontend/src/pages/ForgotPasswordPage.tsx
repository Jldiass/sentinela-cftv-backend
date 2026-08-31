import { ArrowLeft, MailCheck } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { AuthShell } from "../components/AuthShell";

export function ForgotPasswordPage() {
  const [requested, setRequested] = useState(false);

  return (
    <AuthShell>
      <div className="auth-card">
        <div className="auth-card-heading">
          <p className="eyebrow">RECUPERAÇÃO DE ACESSO</p>
          <h2>Redefinir senha</h2>
          <p>Informe seu e-mail corporativo para receber as instruções de redefinição.</p>
        </div>
        {requested ? (
          <div className="auth-notice success">
            <MailCheck size={18} /> Solicitação registrada apenas nesta interface. O envio será ativado quando
            a API de autenticação estiver disponível.
          </div>
        ) : (
          <form
            className="auth-form"
            onSubmit={(event) => {
              event.preventDefault();
              setRequested(true);
            }}
          >
            <label>
              E-mail corporativo
              <span className="auth-input">
                <MailCheck size={17} />
                <input type="email" autoComplete="email" required />
              </span>
            </label>
            <button className="button primary auth-submit">Solicitar redefinição</button>
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
