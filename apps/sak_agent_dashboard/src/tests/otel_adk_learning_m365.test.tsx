import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { GET as otelGet } from "../app/api/otel/route";
import { getOtelData } from "../lib/otel";
import OtelPanel from "../components/OtelPanel";

import { GET as adkGet } from "../app/api/google-adk/route";
import { getAdkData } from "../lib/googleAdk";
import GoogleAdkPanel from "../components/GoogleAdkPanel";

import { GET as learningGet } from "../app/api/gcp-learning/route";
import { getGcpLearningData } from "../lib/gcpLearning";
import GcpLearningPanel from "../components/GcpLearningPanel";

import { GET as m365Get } from "../app/api/m365-copilot/route";
import { getM365CopilotData } from "../lib/m365Copilot";
import M365CopilotPanel from "../components/M365CopilotPanel";

import { getSpecKitData } from "../lib/speckit";
import SpecKitPanel from "../components/SpecKitPanel";

describe("Observability (OpenTelemetry) tab", () => {
  it("returns signals, exporters, semconv, integration snippet", async () => {
    const data = getOtelData();
    expect(data.signals.map((s) => s.id).sort()).toEqual(["logs", "metrics", "traces"]);
    expect(data.exporters.some((e) => e.id === "otlp-grpc")).toBe(true);
    expect(data.llmSemconv.some((a) => a.attribute === "gen_ai.system")).toBe(true);
    expect(data.sakthaiIntegration).toContain("sakthai.agent.loop");
    const res = await otelGet();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.success).toBe(true);
  });
  it("renders overview + signal cards + semconv table", () => {
    render(<OtelPanel data={getOtelData()} />);
    expect(screen.getAllByText(/Observability for Agents/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/TRACES/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("gen_ai.system").length).toBeGreaterThan(0);
  });
  it("renders loading state when null", () => {
    render(<OtelPanel data={null} />);
    expect(screen.getByText(/Loading OTel inventory/i)).toBeInTheDocument();
  });
});

describe("Google ADK tab", () => {
  it("returns install, primitives (llm-agent, workflow-agent, runner), cli commands", async () => {
    const data = getAdkData();
    expect(data.install).toBe("pip install google-adk");
    const kinds = new Set(data.primitives.map((p) => p.kind));
    for (const k of ["llm-agent", "workflow-agent", "runner", "tool", "mcp", "cli"]) {
      expect(kinds.has(k as any)).toBe(true);
    }
    expect(data.cliCommands.some((c) => c.command.startsWith("adk web"))).toBe(true);
    const res = await adkGet();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.success).toBe(true);
  });
  it("renders header + LlmAgent primitive + comparison note", () => {
    render(<GoogleAdkPanel data={getAdkData()} />);
    expect(screen.getByText(/Agent Development Kit for Python/i)).toBeInTheDocument();
    expect(screen.getByText("LlmAgent")).toBeInTheDocument();
    expect(screen.getByText("SequentialAgent")).toBeInTheDocument();
    expect(screen.getByText(/Where this sits vs\. Antigravity/i)).toBeInTheDocument();
  });
});

describe("GCP Learning tab", () => {
  it("exposes curated resources tagged by category", async () => {
    const data = getGcpLearningData();
    expect(data.resources.length).toBeGreaterThanOrEqual(5);
    const paths = data.resources.map((r) => r.path);
    expect(paths).toEqual(
      expect.arrayContaining(["courses/", "quests/", "self-paced-labs/"])
    );
    expect(data.tagLabels.agents).toBeDefined();
    const res = await learningGet();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.success).toBe(true);
  });
  it("filters resources by tag chip", () => {
    const data = getGcpLearningData();
    render(<GcpLearningPanel data={data} />);
    // 'all' selected by default
    expect(screen.getByText("Full GCP courses")).toBeInTheDocument();
    // Click the 'Notebooks' filter
    fireEvent.click(screen.getByRole("button", { name: /Notebooks/i }));
    // The datalab entry is tagged notebooks
    expect(screen.getByText("Datalab notebooks")).toBeInTheDocument();
    // A pure-labs entry should NOT be visible now
    expect(screen.queryByText("Self-paced labs")).toBeNull();
  });
});

describe("M365 Copilot tab", () => {
  it("returns install, primitives, auth steps, contrast rows", async () => {
    const data = getM365CopilotData();
    expect(data.overview.packageName).toBe("microsoft-agents-m365copilot");
    expect(data.install).toContain("microsoft-agents-m365copilot");
    expect(data.install).toContain("azure-identity");
    expect(data.primitives.some((p) => p.name.includes("Retrieval"))).toBe(true);
    expect(data.authSteps.length).toBeGreaterThan(3);
    expect(data.contrastWithTeamsMcp.some((r) => r.dimension === "Auth model")).toBe(true);
    const res = await m365Get();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.success).toBe(true);
  });
  it("renders header + delegated flow + contrast table", () => {
    render(<M365CopilotPanel data={getM365CopilotData()} />);
    expect(screen.getAllByText(/M365 Copilot/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Delegated-auth flow/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/vs\. teams-copilot-mcp/i).length).toBeGreaterThan(0);
  });
});

describe("SpecKit tab — upstream enhancement", () => {
  it("data now carries the upstream block with install command, license, commands, integrations", () => {
    const data = getSpecKitData();
    expect(data.upstream.repoUrl).toBe("https://github.com/github/spec-kit");
    expect(data.upstream.license).toBe("MIT");
    expect(data.upstream.installCommand).toContain("specify-cli");
    const slashes = data.upstream.commands.map((c) => c.slash);
    expect(slashes).toEqual(
      expect.arrayContaining([
        "/speckit.constitution",
        "/speckit.specify",
        "/speckit.plan",
        "/speckit.tasks",
        "/speckit.implement",
        "/speckit.converge",
        "/speckit.taskstoissues",
      ])
    );
    expect(data.upstream.supportedIntegrations.length).toBeGreaterThan(3);
  });
  it("panel renders the Upstream section", () => {
    render(<SpecKitPanel data={getSpecKitData()} />);
    expect(screen.getByText(/Upstream — github\/spec-kit/i)).toBeInTheDocument();
    expect(screen.getByText("/speckit.converge")).toBeInTheDocument();
    expect(screen.getByText(/uv tool install specify-cli/i)).toBeInTheDocument();
  });
});
