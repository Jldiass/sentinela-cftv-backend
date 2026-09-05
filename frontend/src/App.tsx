import {
  Activity,
  BellRing,
  Camera,
  History,
  LayoutDashboard,
  LogOut,
  Moon,
  Radio,
  Settings,
  ShieldCheck,
  Sun,
  Users,
  Video,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { systemApi } from "./api/system";
import { useAuth } from "./auth/useAuth";
import { ServiceStatus } from "./components/Status";
import styles from "./App.module.css";

const nav = [
  ["/", "Visão geral", LayoutDashboard, "overview.read"],
  ["/mosaics", "Mosaicos", Video, "mosaics.read"],
  ["/cameras", "Câmeras", Camera, "cameras.read"],
  ["/history", "Gravações", History, "cameras.read"],
  ["/events", "Eventos", BellRing, "events.read"],
  ["/users", "Usuários", Users, "users.manage"],
  ["/roles", "Perfis e permissões", ShieldCheck, "permissions.manage"],
  ["/health", "Saúde do sistema", Activity, "system.health.read"],
] as const;

export default function App() {
  const [theme, setTheme] = useState<"dark" | "light">(
    () => (localStorage.getItem("malupe-theme") as "dark" | "light" | null) ?? "dark",
  );
  const { user, can, logout } = useAuth();
  const queryClient = useQueryClient();
  const health = useQuery({
    queryKey: ["health"],
    queryFn: systemApi.health,
    refetchInterval: 15_000,
    retry: 1,
    enabled: can("system.health.read"),
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    localStorage.setItem("malupe-theme", theme);
  }, [theme]);
  const leave = async () => {
    await logout();
    queryClient.clear();
  };
  return (
    <div className={styles.shell}>
      <a className="skip-link" href="#main-content">
        Ir para o conteúdo
      </a>
      <aside className="sidebar">
        <div className="brand" translate="no">
          <Radio size={22} aria-hidden="true" />
          <span>
            MALUPE <b>CAM</b>
          </span>
        </div>
        <div className="environment">
          <small>Central ativa</small>
          <strong>{user?.full_name}</strong>
          <span>{user?.roles.join(", ") || "Sem perfil"}</span>
        </div>
        <nav aria-label="Navegação principal">
          {nav
            .filter(([, , , permission]) => can(permission))
            .map(([to, label, Icon]) => (
              <NavLink key={to} to={to} end={to === "/"}>
                <Icon size={18} aria-hidden="true" />
                {label}
              </NavLink>
            ))}
        </nav>
        <div className="sidebar-footer">
          <Settings size={15} aria-hidden="true" />
          <span>API {health.data?.version ?? "--"}</span>
          {can("system.health.read") && <ServiceStatus up={health.data?.ok ?? false} />}
          <button className="theme-toggle" onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}>
            <span>
              {theme === "dark" ? (
                <Sun size={15} aria-hidden="true" />
              ) : (
                <Moon size={15} aria-hidden="true" />
              )}
            </span>
            {theme === "dark" ? "Modo claro" : "Modo escuro"}
          </button>
          <button className="theme-toggle" onClick={() => void leave()}>
            <LogOut size={15} aria-hidden="true" />
            Sair
          </button>
        </div>
      </aside>
      <main className={styles.main} id="main-content" tabIndex={-1}>
        <Outlet />
      </main>
    </div>
  );
}
