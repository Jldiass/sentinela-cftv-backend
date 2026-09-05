import type { Mosaic } from "../types/api";

export function layoutFor(capacity: number) {
  const columns = Math.ceil(Math.sqrt(capacity));
  return { columns, rows: Math.ceil(capacity / columns) };
}

export function mosaicCamera(mosaic: Mosaic, index: number) {
  return mosaic.cameras.find((item) => item.position === index + 1)?.camera;
}
