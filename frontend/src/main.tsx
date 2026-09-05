import { lazy, StrictMode, Suspense, type ComponentType } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./auth/AuthContext";
import { PermissionRoute, ProtectedRoute } from "./auth/ProtectedRoute";
import "./styles/global.css";

const page = <T extends Record<string, unknown>, K extends keyof T>(loader: () => Promise<T>, name: K) =>
  lazy(() => loader().then((module) => ({ default: module[name] as ComponentType })));
const CamerasPage = page(() => import("./pages/CamerasPage"), "CamerasPage");
const EventsPage = page(() => import("./pages/EventsPage"), "EventsPage");
const ForgotPasswordPage = page(() => import("./pages/ForgotPasswordPage"), "ForgotPasswordPage");
const HealthPage = page(() => import("./pages/HealthPage"), "HealthPage");
const HistoryPage = page(() => import("./pages/HistoryPage"), "HistoryPage");
const LoginPage = page(() => import("./pages/LoginPage"), "LoginPage");
const MosaicViewPage = page(() => import("./pages/MosaicViewPage"), "MosaicViewPage");
const MosaicWizardPage = page(() => import("./pages/MosaicWizardPage"), "MosaicWizardPage");
const MosaicsPage = page(() => import("./pages/MosaicsPage"), "MosaicsPage");
const OverviewPage = page(() => import("./pages/OverviewPage"), "OverviewPage");
const RolesPage = page(() => import("./pages/RolesPage"), "RolesPage");
const ResetPasswordPage = page(() => import("./pages/ResetPasswordPage"), "ResetPasswordPage");
const RegisterPage = page(() => import("./pages/RegisterPage"), "RegisterPage");
const UsersPage = page(() => import("./pages/UsersPage"), "UsersPage");

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Suspense fallback={<main className="session-loading">Carregando…</main>}>
            <Routes>
              <Route path="login" element={<LoginPage />} />
              <Route path="forgot-password" element={<ForgotPasswordPage />} />
              <Route path="register" element={<RegisterPage />} />
              <Route path="reset-password" element={<ResetPasswordPage />} />
              <Route element={<ProtectedRoute />}>
                <Route element={<App />}>
                  <Route
                    path="no-access"
                    element={
                      <section className="permission-denied">
                        <div className="empty">
                          <strong>Nenhuma tela liberada</strong>
                          <span>Solicite um perfil de acesso ao administrador.</span>
                        </div>
                      </section>
                    }
                  />
                  <Route element={<PermissionRoute permission="overview.read" />}>
                    <Route index element={<OverviewPage />} />
                  </Route>
                  <Route element={<PermissionRoute permission="mosaics.read" />}>
                    <Route path="mosaics" element={<MosaicsPage />} />
                    <Route path="mosaics/:id" element={<MosaicViewPage />} />
                  </Route>
                  <Route element={<PermissionRoute permission="mosaics.manage" />}>
                    <Route path="mosaics/new" element={<MosaicWizardPage />} />
                    <Route path="mosaics/:id/edit" element={<MosaicWizardPage />} />
                  </Route>
                  <Route element={<PermissionRoute permission="cameras.read" />}>
                    <Route path="cameras" element={<CamerasPage />} />
                    <Route path="history" element={<HistoryPage />} />
                  </Route>
                  <Route path="live" element={<Navigate to="/mosaics" replace />} />
                  <Route element={<PermissionRoute permission="events.read" />}>
                    <Route path="events" element={<EventsPage />} />
                  </Route>
                  <Route element={<PermissionRoute permission="system.health.read" />}>
                    <Route path="health" element={<HealthPage />} />
                  </Route>
                  <Route element={<PermissionRoute permission="users.manage" />}>
                    <Route path="users" element={<UsersPage />} />
                  </Route>
                  <Route element={<PermissionRoute permission="permissions.manage" />}>
                    <Route path="roles" element={<RolesPage />} />
                  </Route>
                </Route>
              </Route>
            </Routes>
          </Suspense>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
