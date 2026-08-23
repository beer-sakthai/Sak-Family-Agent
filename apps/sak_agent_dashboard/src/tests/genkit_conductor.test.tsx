import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { GET as genkitGet } from "../app/api/genkit/route";
import { getGenkitData } from "../lib/genkit";
import GenkitPanel from "../components/GenkitPanel";

import { GET as conductorGet } from "../app/api/conductor/route";
import { getConductorData } from "../lib/conductor";
import ConductorPanel from "../components/ConductorPanel";

describe("Genkit Feature Suite", () => {
  it("data module exposes overview, install, quickstart, primitives, providers, features", async () => {
    const data = getGenkitData();
    expect(data.overview.packageName).toBe("genkit");
    expect(data.install).toContain("uv add genkit");
    expect(data.quickstart).toContain("from genkit.core import Genkit");
    expect(data.primitives.length).toBeGreaterThanOrEqual(5);
    const kinds = new Set(data.primitives.map((p) => p.kind));
    for (const k of ["core", "decorator", "generation"]) {
      expect(kinds.has(k as any)).toBe(true);
    }
    const providerIds = data.providers.map((p) => p.id);
    expect(providerIds).toEqual(
      expect.arrayContaining([
        "google-genai",
        "vertex",
        "anthropic",
        "openai",
        "ollama",
      ])
    );
    expect(data.distinctiveFeatures.length).toBeGreaterThan(0);

    const res = await genkitGet();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.genkit.providers.length).toBe(data.providers.length);
  });

  it("panel renders header, install, quickstart, providers, and primitives", () => {
    const data = getGenkitData();
    render(<GenkitPanel data={data} />);
    expect(screen.getByText(/Genkit — Python/i)).toBeInTheDocument();
    expect(screen.getByText(/uv add genkit/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Google Gemini/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Ollama/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/@ai.tool\(\)/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Quickstart/i)).toBeInTheDocument();
  });

  it("panel renders loading state when data is null", () => {
    render(<GenkitPanel data={null} />);
    expect(screen.getByText(/Loading Genkit SDK inventory/i)).toBeInTheDocument();
  });
});

describe("Conductor Feature Suite", () => {
  it("data module exposes overview, hosts (including recommended Antigravity), commands, artifacts, workflow", async () => {
    const data = getConductorData();
    expect(data.overview.methodology).toMatch(/Spec-Driven/i);
    const hostIds = data.hosts.map((h) => h.id);
    expect(hostIds).toEqual(
      expect.arrayContaining(["antigravity", "claude-code", "live-symlink"])
    );
    const primary = data.hosts.find((h) => h.primary);
    expect(primary?.id).toBe("antigravity");
    expect(data.commands.length).toBeGreaterThanOrEqual(6);
    const slashes = data.commands.map((c) => c.slash);
    expect(slashes).toEqual(
      expect.arrayContaining([
        "/conductor:conductor-setup",
        "/conductor:conductor-new-track",
        "/conductor:conductor-implement",
        "/conductor:conductor-status",
        "/conductor:conductor-revert",
        "/conductor:conductor-review",
      ])
    );
    expect(data.artifacts.some((a) => a.path === "conductor/product.md")).toBe(true);
    expect(
      data.artifacts.some((a) => a.path.includes("tracks/") && a.scope === "track")
    ).toBe(true);
    expect(data.workflow.length).toBeGreaterThan(3);

    const res = await conductorGet();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.conductor.commands.length).toBe(data.commands.length);
  });

  it("panel renders header, host cards, command table, and artifacts", () => {
    const data = getConductorData();
    render(<ConductorPanel data={data} />);
    expect(screen.getByText(/Conductor — Spec-Driven Dev for Agents/i)).toBeInTheDocument();
    expect(screen.getByText(/Antigravity CLI \(agy\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/recommended/i).length).toBeGreaterThan(0);
    expect(screen.getByText("/conductor:conductor-setup")).toBeInTheDocument();
    expect(screen.getByText("/conductor:conductor-review")).toBeInTheDocument();
    expect(screen.getByText("conductor/product.md")).toBeInTheDocument();
    expect(screen.getByText(/Typical cycle/i)).toBeInTheDocument();
    // Cross-reference to SpecKit tab
    expect(screen.getByText(/Relative to the SpecKit tab/i)).toBeInTheDocument();
  });

  it("panel renders loading state when data is null", () => {
    render(<ConductorPanel data={null} />);
    expect(screen.getByText(/Loading Conductor inventory/i)).toBeInTheDocument();
  });
});
