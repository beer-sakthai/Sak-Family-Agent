import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET as streamGET, POST as streamPOST } from "@/app/api/gateway/team/stream/route";
import { TeamPipelineVisualizer } from "@/components/TeamPipelineVisualizer";
import { NextRequest } from "next/server";

describe("TeamPipelineVisualizer & Streaming Route", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  describe("Stream API Route (/api/gateway/team/stream)", () => {
    it("GET proxies SSE event stream from upstream gateway", async () => {
      const mockStream = new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode("event: pipeline_start\ndata: {}\n\n"));
          controller.close();
        },
      });

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockStream,
      });

      const req = new NextRequest("http://localhost:3000/api/gateway/team/stream?pipeline=code-review&task=Test");
      const res = await streamGET(req);
      expect(res.headers.get("content-type")).toContain("text/event-stream");
    });

    it("POST proxies JSON body to upstream gateway stream", async () => {
      const mockStream = new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode("event: step_token\ndata: {}\n\n"));
          controller.close();
        },
      });

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockStream,
      });

      const req = new NextRequest("http://localhost:3000/api/gateway/team/stream", {
        method: "POST",
        body: JSON.stringify({ pipeline: "code-review", task: "Review PR" }),
      });
      const res = await streamPOST(req);
      expect(res.headers.get("content-type")).toContain("text/event-stream");
    });
  });

  describe("TeamPipelineVisualizer Component", () => {
    it("renders pipeline buttons and initial DAG stage nodes", () => {
      render(<TeamPipelineVisualizer />);

      expect(screen.getByText("Live Multi-Agent Pipeline & DAG Visualizer")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /code-review/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /research-brief/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /incident-response/i })).toBeInTheDocument();

      // Check initial stage cards for code-review
      expect(screen.getByText("code-analysis")).toBeInTheDocument();
      expect(screen.getByText("ci-validation")).toBeInTheDocument();
      expect(screen.getByText("test-synthesis")).toBeInTheDocument();
    });

    it("switches pipeline when clicking a pipeline selector button", () => {
      render(<TeamPipelineVisualizer />);

      const researchBtn = screen.getByRole("button", { name: /research-brief/i });
      fireEvent.click(researchBtn);

      expect(screen.getByText("topic-framing")).toBeInTheDocument();
      expect(screen.getByText("web-recon")).toBeInTheDocument();
      expect(screen.getByText("briefing-synthesis")).toBeInTheDocument();
    });

    it("allows editing task prompt and triggers execution button", async () => {
      render(<TeamPipelineVisualizer />);

      const textarea = screen.getByLabelText(/Execution Task Prompt:/i) as HTMLTextAreaElement;
      fireEvent.change(textarea, { target: { value: "New custom analysis prompt" } });
      expect(textarea.value).toBe("New custom analysis prompt");

      const execBtn = screen.getByText("Execute Live Pipeline");
      expect(execBtn).toBeInTheDocument();
      expect(execBtn).not.toBeDisabled();
    });
  });
});
