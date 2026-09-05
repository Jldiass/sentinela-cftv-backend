import { afterEach, describe, expect, it, vi } from "vitest";
import { messageFromPayload, request, setAccessToken } from "./client";
afterEach(() => {
  vi.unstubAllGlobals();
  setAccessToken(null);
});
describe("messageFromPayload", () => {
  it("prioriza erro devolvido pela API", () =>
    expect(messageFromPayload(409, { detail: "Limite atingido" })).toBe("Limite atingido"));
  it("traduz erro sem payload", () => expect(messageFromPayload(503, {})).toContain("indisponível"));
});

describe("sessão", () => {
  it("compartilha um único refresh e repete chamadas 401 uma vez", async () => {
    setAccessToken("expirado");
    let protectedCalls = 0;
    let refreshCalls = 0;
    const fetchMock = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/refresh")) {
        refreshCalls += 1;
        return new Response(
          JSON.stringify({ access_token: "novo", token_type: "bearer", expires_in: 900, user: {} }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      protectedCalls += 1;
      if (protectedCalls <= 2)
        return new Response(JSON.stringify({ detail: "expirado" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        });
      expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer novo");
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      Promise.all([request<{ ok: boolean }>("/a"), request<{ ok: boolean }>("/b")]),
    ).resolves.toEqual([{ ok: true }, { ok: true }]);
    expect(refreshCalls).toBe(1);
  });
});
