import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import App from "./App";
import { OverviewPage } from "./pages/OverviewPage";
import { LivePage } from "./pages/LivePage";
import { CamerasPage } from "./pages/CamerasPage";
import { HistoryPage } from "./pages/HistoryPage";
import { EventsPage } from "./pages/EventsPage";
import { HealthPage } from "./pages/HealthPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { LoginPage } from "./pages/LoginPage";
import "./styles/global.css";
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="login" element={<LoginPage />} />
          <Route path="forgot-password" element={<ForgotPasswordPage />} />
          <Route element={<App />}>
            <Route index element={<OverviewPage />} />
            <Route path="live" element={<LivePage />} />
            <Route path="cameras" element={<CamerasPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="events" element={<EventsPage />} />
            <Route path="health" element={<HealthPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
