import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { GET as mcpSdkGet } from "../app/api/mcp-sdk/route";
import { getMcpSdkData } from "../lib/mcpSdk";
import McpSdkPanel from "../components/McpSdkPanel";

describe("MCP SDK Feature Suite", () => {
  describe("getMcpSdkData + /api/mcp-sdk", () => {
    it("returns overview, both packages, primitives, and scaffold files", async () => {
      const data = getMcpSdkData();
      expect(data.overview.protocolVersion).toBe("2024-11-05");
      expect(data.overview.docsUrl).toContain(
        "modelcontextprotocol/python-sdk"
      );
      const pkgNames = data.packages.map((p) => p.name);
      expect(pkgNames).toEqual(expect.arrayContaining(["mcp", "fastmcp"]));
      expect(data.primitives.length).toBeGreaterThanOrEqual(6);
      const kinds = data.primitives.map((p) => p.kind);
      expect(kinds).toEqual(
        expect.arrayContaining([
          "server",
          "tool",
          "resource",
          "prompt",
          "transport",
          "client",
        ])
      );
      expect(data.scaffold.files.length).toBeGreaterThan(0);
      const scaffoldPaths = data.scaffold.files.map((f) => f.path);
      expect(
        scaffoldPaths.some((p) => p.endsWith("pyproject.toml"))
      ).toBe(true);
      expect(scaffoldPaths.some((p) => p.endsWith("server.py"))).toBe(true);
      expect(scaffoldPaths.some((p) => p.endsWith(".mcp.json"))).toBe(true);

      const res = await mcpSdkGet();
      expect(res.status).toBe(200);
      const json = await res.json();
      expect(json.success).toBe(true);
      expect(json.sdk.packages.length).toBeGreaterThan(0);
    });

    it("detects fastmcp usage inside services/teams-copilot-mcp", () => {
      const data = getMcpSdkData();
      const teamsSite = data.usageSites.find((s) =>
        s.path.startsWith("services/teams-copilot-mcp/")
      );
      expect(teamsSite).toBeDefined();
    });

    it("marks fastmcp as pinned via detectedVersionSpec when pyproject is present", () => {
      const data = getMcpSdkData();
      const fastmcp = data.packages.find((p) => p.name === "fastmcp");
      expect(fastmcp).toBeDefined();
      // In a normal checkout of this repo, services/teams-copilot-mcp
      // pins fastmcp>=2.0.0, so the spec must be detected.
      expect(fastmcp?.detectedVersionSpec).toBeDefined();
      expect(fastmcp?.detectedVersionSpec).toMatch(/^[><=~!]/);
    });
  });

  describe("<McpSdkPanel /> component", () => {
    it("renders overview, package cards, and primitives", () => {
      const data = getMcpSdkData();
      render(<McpSdkPanel data={data} />);
      expect(
        screen.getAllByText(/Model Context Protocol/i).length
      ).toBeGreaterThan(0);
      // Package names (as <code> elements) — allow multiple matches
      expect(screen.getAllByText("mcp").length).toBeGreaterThan(0);
      expect(screen.getAllByText("fastmcp").length).toBeGreaterThan(0);
      expect(screen.getByText("FastMCP server")).toBeInTheDocument();
      expect(screen.getByText("@mcp.tool()")).toBeInTheDocument();
      expect(
        screen.getByText(/Scaffold: new MCP server/i)
      ).toBeInTheDocument();
    });

    it("renders a loading state when data is null", () => {
      render(<McpSdkPanel data={null} />);
      expect(screen.getByText(/Loading SDK inventory/i)).toBeInTheDocument();
    });
  });
});
