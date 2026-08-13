import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach } from "vitest";

import { GET as mcpServersGet } from "../app/api/mcp-servers/route";
import { getMcpServers, summarizeActions } from "../lib/mcpServers";
import McpServers from "../components/McpServers";

const ENV_KEYS = [
  "MSGRAPH_TENANT_ID",
  "MSGRAPH_CLIENT_ID",
  "MSGRAPH_CLIENT_SECRET",
] as const;

describe("MCP Servers Feature Suite", () => {
  let savedEnv: Record<string, string | undefined>;

  beforeEach(() => {
    savedEnv = {} as Record<string, string | undefined>;
    for (const k of ENV_KEYS) {
      savedEnv[k] = process.env[k];
      delete process.env[k];
    }
  });

  afterEach(() => {
    for (const k of ENV_KEYS) {
      if (savedEnv[k] === undefined) {
        delete process.env[k];
      } else {
        process.env[k] = savedEnv[k]!;
      }
    }
  });

  describe("GET /api/mcp-servers", () => {
    it("returns the teams-copilot-mcp server with a non-empty action catalog", async () => {
      const res = await mcpServersGet();
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data.success).toBe(true);
      expect(Array.isArray(data.servers)).toBe(true);
      expect(data.servers.length).toBeGreaterThan(0);
      const teams = data.servers.find((s: any) => s.id === "teams-copilot-mcp");
      expect(teams).toBeDefined();
      expect(teams.transport).toBe("stdio");
      expect(Array.isArray(teams.actions)).toBe(true);
      expect(teams.actions.length).toBeGreaterThanOrEqual(15);
      expect(Array.isArray(teams.envVars)).toBe(true);
      expect(teams.envVars.map((e: any) => e.key)).toEqual(
        expect.arrayContaining(ENV_KEYS.map((k) => k)),
      );
    });

    it("reports unconfigured status when no MSGRAPH_* env vars are set", async () => {
      const servers = getMcpServers();
      expect(servers[0].status).toBe("unconfigured");
      expect(servers[0].statusReason).toMatch(/No Microsoft Graph credentials/i);
    });

    it("reports healthy status when all three credentials are set", async () => {
      process.env.MSGRAPH_TENANT_ID = "tenant-xyz";
      process.env.MSGRAPH_CLIENT_ID = "client-abc";
      process.env.MSGRAPH_CLIENT_SECRET = "secret-123";
      const servers = getMcpServers();
      expect(servers[0].status).toBe("healthy");
    });

    it("reports degraded status when only some credentials are set", async () => {
      process.env.MSGRAPH_TENANT_ID = "tenant-xyz";
      process.env.MSGRAPH_CLIENT_ID = "client-abc";
      // secret missing on purpose
      const servers = getMcpServers();
      expect(servers[0].status).toBe("degraded");
      expect(servers[0].statusReason).toMatch(/MSGRAPH_CLIENT_SECRET/);
    });

    it("summarizeActions returns totals, per-category counts, and flags", async () => {
      const [server] = getMcpServers();
      const summary = summarizeActions(server);
      expect(summary.total).toBe(server.actions.length);
      expect(summary.delegatedOnly).toBeGreaterThan(0);
      expect(summary.byCategory.teams).toBeGreaterThan(0);
      expect(summary.byCategory.copilot).toBeGreaterThan(0);
      expect(summary.verify).toBeGreaterThan(0);
    });
  });

  describe("<McpServers /> component", () => {
    it("renders empty-state when no servers are provided", () => {
      render(<McpServers servers={[]} />);
      expect(screen.getByText(/MCP Servers \(0\)/i)).toBeInTheDocument();
      expect(screen.getByText(/No MCP servers registered/i)).toBeInTheDocument();
    });

    it("renders the teams-copilot server card with header, catalog, and snippets", () => {
      const servers = getMcpServers();
      render(<McpServers servers={servers} />);
      expect(screen.getByText(/Teams \+ M365 Copilot/i)).toBeInTheDocument();
      expect(screen.getByText("send_channel_message")).toBeInTheDocument();
      expect(screen.getByText("copilot_retrieval_query")).toBeInTheDocument();
      expect(screen.getByText("MSGRAPH_TENANT_ID")).toBeInTheDocument();
      expect(
        screen.getByText(/SakThai global outbound MCP/i)
      ).toBeInTheDocument();
    });

    it("filters the action catalog by search query", () => {
      const servers = getMcpServers();
      render(<McpServers servers={servers} />);
      const input = screen.getByPlaceholderText(/Search actions/i);
      fireEvent.change(input, { target: { value: "calendar" } });
      // list_calendar_events should still be visible; list_channels should not
      expect(screen.getByText("list_calendar_events")).toBeInTheDocument();
      expect(screen.queryByText("list_channels")).toBeNull();
    });

    it("Delegated-only toggle narrows the catalog to delegated-auth actions", () => {
      const servers = getMcpServers();
      render(<McpServers servers={servers} />);
      const toggle = screen.getByRole("button", { name: /Delegated-only/i });
      fireEvent.click(toggle);
      // copilot_retrieval_query is the only delegated-auth action today
      expect(screen.getByText("copilot_retrieval_query")).toBeInTheDocument();
      expect(screen.queryByText("list_channels")).toBeNull();
    });
  });
});
