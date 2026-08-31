import {
  Activity,
  BellRing,
  Camera,
  History,
  LayoutDashboard,
  MonitorPlay,
  Moon,
  Radio,
  Settings,
  Sun,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { systemApi } from "./api/system";
import styles from "./App.module.css";
import { ServiceStatus } from "./components/Status";
const nav = [
  ["/", "Visão geral", LayoutDashboard],
  ["/live", "Ao vivo", MonitorPlay],
  ["/cameras", "Câmeras", Camera],
  ["/history", "Histórico", History],
  ["/events", "Eventos", BellRing],
  ["/health", "Saúde do sistema", Activity],
] as const;
export default function App() {
  const [theme, setTheme] = useState<"dark" | "light">(
    () => (localStorage.getItem("malupe-theme") as "dark" | "light" | null) ?? "dark",
  );
  const health = useQuery({
    queryKey: ["health"],
    queryFn: systemApi.health,
    refetchInterval: 15_000,
    retry: 1,
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("malupe-theme", theme);
  }, [theme]);
  return (
    <div className={styles.shell}>
      <aside className="sidebar">
        <div className="brand">
          <Radio size={22} />
          <span>
            MALUPE <b>CAM</b>
          </span>
        </div>
        <div className="environment">
          <small>OPERAÇÃO LOCAL</small>
          <strong>Central de monitoramento</strong>
        </div>
        <nav>
          {nav.map(([to, label, Icon]) => (
            <NavLink key={to} to={to} end={to === "/"}>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <Settings size={15} />
          <span>API {health.data?.version ?? "--"}</span>
          <ServiceStatus up={health.data?.ok ?? false} />
          <button
            className="theme-toggle"
            onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
            title={theme === "dark" ? "Ativar modo claro" : "Ativar modo escuro"}
            aria-label={theme === "dark" ? "Ativar modo claro" : "Ativar modo escuro"}
          >
            {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
            <span>{theme === "dark" ? "Claro" : "Escuro"}</span>
          </button>
        </div>
      </aside>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
