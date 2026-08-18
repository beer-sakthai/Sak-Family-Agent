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
      expect(data.servers.length).toBeGreaterThanOrEqual(2);
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

    it("returns the Composio hosted server with HTTP transport, no local env, and its 6 meta-tools", async () => {
      const res = await mcpServersGet();
      const data = await res.json();
      const composio = data.servers.find((s: any) => s.id === "composio");
      expect(composio).toBeDefined();
      expect(composio.transport).toBe("http");
      expect(composio.actions).toEqual([]);
      expect(composio.envVars).toEqual([]);
      expect(composio.status).toBe("healthy");
      const toolNames = composio.tools.map((t: any) => t.name);
      expect(toolNames).toEqual(
        expect.arrayContaining([
          "COMPOSIO_SEARCH_TOOLS",
          "COMPOSIO_MANAGE_CONNECTIONS",
          "COMPOSIO_WAIT_FOR_CONNECTIONS",
          "COMPOSIO_MULTI_EXECUTE_TOOL",
          "COMPOSIO_REMOTE_WORKBENCH",
          "COMPOSIO_REMOTE_BASH_TOOL",
        ])
      );
      expect(composio.entrypoint).toBe("https://connect.composio.dev/mcp");
      expect(
        composio.registrationTargets.some(
          (t: any) => t.label.startsWith("Cursor")
        )
      ).toBe(true);
    });

    it("reports unconfigured status for teams-copilot when no MSGRAPH_* env vars are set", async () => {
      const servers = getMcpServers();
      const teams = servers.find((s) => s.id === "teams-copilot-mcp")!;
      expect(teams.status).toBe("unconfigured");
      expect(teams.statusReason).toMatch(/No Microsoft Graph credentials/i);
    });

    it("reports healthy status for teams-copilot when all three credentials are set", async () => {
      process.env.MSGRAPH_TENANT_ID = "tenant-xyz";
      process.env.MSGRAPH_CLIENT_ID = "client-abc";
      process.env.MSGRAPH_CLIENT_SECRET = "secret-123";
      const servers = getMcpServers();
      const teams = servers.find((s) => s.id === "teams-copilot-mcp")!;
      expect(teams.status).toBe("healthy");
    });

    it("reports degraded status for teams-copilot when only some credentials are set", async () => {
      process.env.MSGRAPH_TENANT_ID = "tenant-xyz";
      process.env.MSGRAPH_CLIENT_ID = "client-abc";
      // secret missing on purpose
      const servers = getMcpServers();
      const teams = servers.find((s) => s.id === "teams-copilot-mcp")!;
      expect(teams.status).toBe("degraded");
      expect(teams.statusReason).toMatch(/MSGRAPH_CLIENT_SECRET/);
    });

    it("keeps Composio healthy regardless of MSGRAPH_* env state", async () => {
      const servers = getMcpServers();
      const composio = servers.find((s) => s.id === "composio")!;
      expect(composio.status).toBe("healthy");
    });

    it("summarizeActions returns totals, per-category counts, and flags", async () => {
      const servers = getMcpServers();
      const teams = servers.find((s) => s.id === "teams-copilot-mcp")!;
      const summary = summarizeActions(teams);
      expect(summary.total).toBe(teams.actions.length);
      expect(summary.delegatedOnly).toBeGreaterThan(0);
      expect(summary.byCategory.teams).toBeGreaterThan(0);
      expect(summary.byCategory.copilot).toBeGreaterThan(0);
      expect(summary.verify).toBeGreaterThan(0);
    });

    it("summarizeActions handles servers with no catalog (Composio)", async () => {
      const servers = getMcpServers();
      const composio = servers.find((s) => s.id === "composio")!;
      const summary = summarizeActions(composio);
      expect(summary.total).toBe(0);
      expect(summary.delegatedOnly).toBe(0);
      expect(summary.verify).toBe(0);
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
      expect(screen.getAllByText("send_channel_message").length).toBeGreaterThan(0);
      expect(screen.getAllByText("copilot_retrieval_query").length).toBeGreaterThan(0);
      expect(screen.getByText("MSGRAPH_TENANT_ID")).toBeInTheDocument();
      expect(
        screen.getAllByText(/SakThai global outbound MCP/i).length
      ).toBeGreaterThan(0);
    });

    it("renders the Composio card with meta-tools and skips the Graph action catalog", () => {
      const servers = getMcpServers();
      render(<McpServers servers={servers} />);
      expect(screen.getByText(/Composio \(1000\+ SaaS apps\)/i)).toBeInTheDocument();
      expect(screen.getByText("COMPOSIO_SEARCH_TOOLS")).toBeInTheDocument();
      expect(screen.getByText("COMPOSIO_MULTI_EXECUTE_TOOL")).toBeInTheDocument();
      // The tab header should count both servers
      expect(screen.getByText(/MCP Servers \(2\)/i)).toBeInTheDocument();
    });

    it("filters the action catalog by search query", () => {
      const servers = getMcpServers();
      render(<McpServers servers={servers} />);
      // list_channels appears in both the tools list and the action catalog before filtering
      const beforeCount = screen.getAllByText("list_channels").length;
      expect(beforeCount).toBeGreaterThanOrEqual(2);
      const input = screen.getByPlaceholderText(/Search actions/i);
      fireEvent.change(input, { target: { value: "calendar" } });
      // list_calendar_events should still be visible in the filtered catalog
      expect(screen.getAllByText("list_calendar_events").length).toBeGreaterThan(0);
      // list_channels should be removed from the catalog (tools list copy remains)
      expect(screen.getAllByText("list_channels").length).toBeLessThan(beforeCount);
    });

    it("Delegated-only toggle narrows the catalog to delegated-auth actions", () => {
      const servers = getMcpServers();
      render(<McpServers servers={servers} />);
      const beforeCount = screen.getAllByText("list_channels").length;
      const toggle = screen.getByRole("button", { name: /Delegated-only/i });
      fireEvent.click(toggle);
      // copilot_retrieval_query is the only delegated-auth action today
      expect(screen.getAllByText("copilot_retrieval_query").length).toBeGreaterThan(0);
      // list_channels is app-only and should drop out of the catalog after toggle
      expect(screen.getAllByText("list_channels").length).toBeLessThan(beforeCount);
    });
  });
});
