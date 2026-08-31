import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CameraStatusBadge } from "./Status";
describe("CameraStatusBadge", () => {
  it("apresenta estado online", () => {
    render(<CameraStatusBadge status="online" />);
    expect(screen.getByText("Online")).toBeInTheDocument();
  });
});
