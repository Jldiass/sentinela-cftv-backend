import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./useAuth";

export function ProtectedRoute() {
  const { user, ready } = useAuth();
  const location = useLocation();
  if (!ready)
    return (
      <main className="session-loading" aria-live="polite">
        Verificando sessão…
      </main>
    );
  return user ? <Outlet /> : <Navigate to="/login" replace state={{ from: location.pathname }} />;
}

export function PermissionRoute({ permission }: { permission: string }) {
  const { can } = useAuth();
  return can(permission) ? (
    <Outlet />
  ) : (
    <section className="permission-denied" aria-labelledby="permission-heading">
      <div className="empty permission-denied">
        <strong id="permission-heading">Acesso não autorizado</strong>
        <span>Solicite esta permissão ao administrador da central.</span>
      </div>
    </section>
  );
}
