import { Moon, Radio, ShieldCheck, Sun } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

export function AuthShell({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<"dark" | "light">(
    () => (localStorage.getItem("malupe-theme") as "dark" | "light" | null) ?? "dark",
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("malupe-theme", theme);
  }, [theme]);

  return (
    <main className="auth-shell">
      <button
        className="auth-theme-toggle"
        onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
        aria-label={theme === "dark" ? "Ativar modo claro" : "Ativar modo escuro"}
      >
        {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        {theme === "dark" ? "Modo claro" : "Modo escuro"}
      </button>
      <section className="auth-intro">
        <div className="brand">
          <Radio size={24} />
          <span>
            MALUPE <b>CAM</b>
          </span>
        </div>
        <div className="auth-intro-copy">
          <p className="eyebrow">CENTRAL DE SEGURANÇA</p>
          <h1>Controle operacional de vídeo.</h1>
          <p>Acesso restrito à central de câmeras, histórico de gravações e ocorrências de segurança.</p>
        </div>
        <div className="auth-assurance">
          <ShieldCheck size={18} />
          <div>
            <strong>Ambiente monitorado</strong>
            <span>As ações operacionais são registradas.</span>
          </div>
        </div>
      </section>
      <section className="auth-form-area">{children}</section>
    </main>
  );
}
