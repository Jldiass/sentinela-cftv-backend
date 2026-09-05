import { describe, expect, it } from "vitest";
import { layoutFor, mosaicCamera } from "./mosaic";
import type { Mosaic } from "../types/api";
describe("layout de mosaico", () => {
  it.each([
    [1, 1, 1],
    [2, 2, 1],
    [4, 2, 2],
    [9, 3, 3],
    [17, 5, 4],
    [36, 6, 6],
  ])("distribui %i posições em %ix%i", (capacity, columns, rows) =>
    expect(layoutFor(capacity)).toEqual({ columns, rows }),
  );
  it("respeita a posição persistida da câmera", () => {
    const camera = { id: 7, name: "Portaria" } as Mosaic["cameras"][number]["camera"];
    const mosaic = { cameras: [{ camera_id: 7, position: 2, camera }] } as Mosaic;
    expect(mosaicCamera(mosaic, 0)).toBeUndefined();
    expect(mosaicCamera(mosaic, 1)).toBe(camera);
  });
});
