import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Credentials } from "./Credentials";

describe("Credentials", () => {
  it("separa servidor, chave e URL completa sem duplicar a chave", () => {
    const streamKey = "cam-chave-teste";
    const server = "rtmp://192.168.1.29:1935";
    const fullUrl = `${server}/${streamKey}`;

    render(
      <Credentials
        credentials={{
          camera_id: 1,
          stream_key: streamKey,
          stream_path: `live/${streamKey}`,
          rtmp_server_url: server,
          rtmp_url: fullUrl,
          hls_url: "http://localhost/hls/cam-chave-teste/index.m3u8",
        }}
        onRotate={vi.fn()}
        rotating={false}
      />,
    );

    expect(screen.getByText("URL para Mibo — campo “URL RTMP”")).toBeInTheDocument();
    expect(screen.getByText("Outro equipamento com campos separados")).toBeInTheDocument();
    expect(screen.getByText(server)).toBeInTheDocument();
    expect(screen.getByText(streamKey)).toBeInTheDocument();
    expect(screen.getByText(fullUrl)).toBeInTheDocument();
    expect(fullUrl.split(streamKey)).toHaveLength(2);
  });
});
