import { layoutFor } from "../utils/mosaic";
export function MosaicGlyph({ capacity }: { capacity: number }) {
  const layout = layoutFor(capacity);
  return (
    <span
      className="mosaic-glyph"
      style={{ gridTemplateColumns: `repeat(${layout.columns}, 1fr)` }}
      aria-label={`Layout para ${capacity} câmeras`}
    >
      {Array.from({ length: Math.min(capacity, 36) }, (_, index) => (
        <i key={index} />
      ))}
    </span>
  );
}
