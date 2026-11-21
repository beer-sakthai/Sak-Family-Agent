import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET as healthGET } from "@/app/api/gateway/health/route";
import { GET as toolsGET, POST as toolsPOST } from "@/app/api/gateway/tools/route";
import { POST as chatPOST } from "@/app/api/gateway/chat/route";
import GatewayPlayground from "@/components/GatewayPlayground";

describe("Gateway API Routes", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  describe("GET /api/gateway/health", () => {
    it("returns healthy payload when runtime gateway responds 200", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "ok", gateway: "sakthai-runtime-gateway", uptime_seconds: 42 }),
      });

      const res = await healthGET();
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.ok).toBe(true);
      expect(data.status).toBe("ok");
      expect(data.gateway).toBe("sakthai-runtime-gateway");
    });

    it("returns offline message gracefully when runtime gateway is unreachable", async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error("ECONNREFUSED"));

      const res = await healthGET();
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.ok).toBe(false);
      expect(data.status).toBe("offline");
      expect(data.message).toContain("Gateway is offline");
    });
  });

  describe("Tools API (/api/gateway/tools)", () => {
    it("GET proxies tool list from upstream runtime gateway", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          tools: [
            {
              type: "function",
              function: { name: "test_tool", description: "A test tool", parameters: {} },
            },
          ],
        }),
      });

      const res = await toolsGET();
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.tools).toHaveLength(1);
      expect(data.tools[0].function.name).toBe("test_tool");
    });

    it("POST executes tool and forwards status code", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: "success", tool: "read_file", result: "file contents" }),
      });

      const req = new Request("http://localhost/api/gateway/tools", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool: "read_file", arguments: { path: "README.md" } }),
      });

      const res = await toolsPOST(req);
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.status).toBe("success");
      expect(data.result).toBe("file contents");
    });
  });

  describe("Chat API (/api/gateway/chat)", () => {
    it("POST handles non-streaming completions request", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          id: "chatcmpl-test",
          object: "chat.completion",
          choices: [
            {
              message: { role: "assistant", content: "Hello from SakThai gateway!" },
              finish_reason: "stop",
            },
          ],
        }),
      });

      const req = new Request("http://localhost/api/gateway/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{ role: "user", content: "Hello" }],
          model: "sakthai:flash",
          stream: false,
        }),
      });

      const res = await chatPOST(req);
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.choices[0].message.content).toBe("Hello from SakThai gateway!");
    });
  });
});

describe("GatewayPlayground UI Component", () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/api/gateway/health")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            ok: true,
            status: "ok",
            gateway: "sakthai-runtime-gateway",
            active_persona: "sakthai",
            allowed_origins: ["*"],
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      });
    });
  });

  it("renders persona switchers and tier preset selectors", async () => {
    render(<GatewayPlayground />);

    expect(screen.getByText("Runtime Gateway")).toBeInTheDocument();
    expect(screen.getByText("SakThai")).toBeInTheDocument();
    expect(screen.getByText("SakSee")).toBeInTheDocument();
    expect(screen.getByText("SakJules")).toBeInTheDocument();
    expect(screen.getByText("SakKing")).toBeInTheDocument();
    expect(screen.getByText("SakSit")).toBeInTheDocument();
    expect(screen.getByText("SakTan")).toBeInTheDocument();

    // Check tier buttons
    expect(screen.getByText("Persona Default")).toBeInTheDocument();
    expect(screen.getByText(/Fast/i)).toBeInTheDocument();
    expect(screen.getByText(/Reasoning/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Local/i).length).toBeGreaterThanOrEqual(1);
  });

  it("switches persona when clicking persona badge", async () => {
    render(<GatewayPlayground />);

    const thaiBtn = screen.getByRole("button", { name: /SakThai/i });
    fireEvent.click(thaiBtn);

    expect(screen.getByText(/Chatting with SakThai/i)).toBeInTheDocument();
  });

  it("changes model tier when clicking tier buttons", async () => {
    render(<GatewayPlayground />);

    const fastBtn = screen.getByRole("button", { name: /Fast/i });
    fireEvent.click(fastBtn);

    expect(screen.getAllByText(/gemini-2.5-flash/i).length).toBeGreaterThanOrEqual(1);
  });

  it("renders guardrail test action buttons", () => {
    render(<GatewayPlayground />);

    expect(screen.getByRole("button", { name: /Destructive: rm -rf \//i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Safe: echo/i })).toBeInTheDocument();
  });
});
