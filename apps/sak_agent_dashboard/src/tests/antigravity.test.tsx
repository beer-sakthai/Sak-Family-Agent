import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { GET as antigravityGet } from "../app/api/antigravity/route";
import { getAntigravityData } from "../lib/antigravity";
import AntigravityPanel from "../components/AntigravityPanel";

describe("Antigravity Feature Suite", () => {
  describe("getAntigravityData + /api/antigravity", () => {
    it("returns overview, install, quickstart, primitives, features, and comparison", async () => {
      const data = getAntigravityData();
      expect(data.overview.packageName).toBe("google-antigravity");
      expect(data.overview.license).toMatch(/Apache/i);
      expect(data.overview.pypiUrl).toContain("google-antigravity");
      expect(data.install.pypi).toBe("pip install google-antigravity");
      expect(data.install.warning).toMatch(/wheel/i);
      expect(data.quickstart).toContain("from google.antigravity import");
      expect(data.primitives.length).toBeGreaterThanOrEqual(6);
      expect(data.features.length).toBeGreaterThanOrEqual(5);
      expect(data.comparison.length).toBeGreaterThanOrEqual(3);

      const res = await antigravityGet();
      expect(res.status).toBe(200);
      const json = await res.json();
      expect(json.success).toBe(true);
      expect(json.antigravity.primitives.length).toBe(data.primitives.length);
    });

    it("covers the key primitive kinds (agent, config, conversation, response, tool, hook, mcp)", () => {
      const data = getAntigravityData();
      const kinds = new Set(data.primitives.map((p) => p.kind));
      for (const k of ["agent", "config", "conversation", "response", "tool", "hook", "mcp"]) {
        expect(kinds.has(k as any)).toBe(true);
      }
    });

    it("comparison table names Antigravity, ChatKit, and MCP SDK for each dimension", () => {
      const data = getAntigravityData();
      for (const row of data.comparison) {
        expect(row.antigravity.length).toBeGreaterThan(0);
        expect(row.chatkit.length).toBeGreaterThan(0);
        expect(row.mcpSdk.length).toBeGreaterThan(0);
      }
    });
  });

  describe("<AntigravityPanel /> component", () => {
    it("renders header, install warning, quickstart, primitives, and comparison", () => {
      const data = getAntigravityData();
      render(<AntigravityPanel data={data} />);
      expect(
        screen.getByText(/Google Antigravity — Python SDK/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Wheels only — cloning the repo is not enough/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/Quickstart/i)).toBeInTheDocument();
      expect(screen.getByText("Agent")).toBeInTheDocument();
      expect(screen.getByText("LocalAgentConfig")).toBeInTheDocument();
      expect(screen.getAllByText("Policy hooks").length).toBeGreaterThan(0);
      expect(
        screen.getByText(/Where this sits vs\. the other SDK tabs/i)
      ).toBeInTheDocument();
    });

    it("renders a loading state when data is null", () => {
      render(<AntigravityPanel data={null} />);
      expect(
        screen.getByText(/Loading Antigravity SDK inventory/i)
      ).toBeInTheDocument();
    });
  });
});
