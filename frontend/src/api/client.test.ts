import { describe, expect, it } from "vitest";
import { messageFromPayload } from "./client";
describe("messageFromPayload", () => {
  it("prioriza erro devolvido pela API", () =>
    expect(messageFromPayload(409, { detail: "Limite atingido" })).toBe("Limite atingido"));
  it("traduz erro sem payload", () => expect(messageFromPayload(503, {})).toContain("mídia"));
});
