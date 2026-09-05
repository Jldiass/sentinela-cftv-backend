import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { Buffer } from "node:buffer";
import { timingSafeEqual } from "node:crypto";

function safeEqual(a: string, b: string) {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  return bufA.length === bufB.length && timingSafeEqual(bufA, bufB);
}

function previewBasicAuth() {
  return {
    name: "malupe-preview-basic-auth",
    configurePreviewServer(server: {
      middlewares: {
        use: (
          middleware: (
            request: { headers: { authorization?: string } },
            response: {
              statusCode: number;
              setHeader: (name: string, value: string) => void;
              end: (body: string) => void;
            },
            next: () => void,
          ) => void,
        ) => void;
      };
    }) {
      const username = process.env.MALUPE_PUBLIC_USER;
      const password = process.env.MALUPE_PUBLIC_PASSWORD;
      if (!username || !password) return;

      const expected = `Basic ${Buffer.from(`${username}:${password}`).toString("base64")}`;
      server.middlewares.use((request, response, next) => {
        if (request.headers.authorization && safeEqual(request.headers.authorization, expected)) {
          next();
          return;
        }
        response.statusCode = 401;
        response.setHeader("WWW-Authenticate", 'Basic realm="Malupe Cam"');
        response.setHeader("Cache-Control", "no-store");
        response.end("Autenticação necessária.");
      });
    },
  };
}

const localProxy = {
  "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
  "/health": { target: "http://127.0.0.1:8000", changeOrigin: true },
  "/hls": {
    target: "http://127.0.0.1:8888",
    changeOrigin: true,
    rewrite: (path: string) => path.replace(/^\/hls/, ""),
  },
  "/playback": {
    target: "http://127.0.0.1:9996",
    changeOrigin: true,
    rewrite: (path: string) => path.replace(/^\/playback/, ""),
  },
};

export default defineConfig({
  plugins: [react(), previewBasicAuth()],
  preview: {
    host: "127.0.0.1",
    port: 4173,
    allowedHosts: [".trycloudflare.com"],
    proxy: localProxy,
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    exclude: ["e2e/**", "node_modules/**", "dist/**"],
  },
});
