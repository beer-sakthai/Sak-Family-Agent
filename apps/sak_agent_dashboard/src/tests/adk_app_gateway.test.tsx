import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { getAdkData } from "../lib/googleAdk";
import GoogleAdkPanel from "../components/GoogleAdkPanel";

import { GET as gatewayGet } from "../app/api/agent-gateway/route";
import { getGatewayData } from "../lib/agentGateway";
import AgentGatewayPanel from "../components/AgentGatewayPanel";

import { getGcpLearningData, GCP_LEARNING_STALENESS_NOTES } from "../lib/gcpLearning";

/**
 * Regression tests for the ADK API-correctness fixes. The first shipped
 * version of this tab carried invented signatures; these assertions pin the
 * real ones so a future edit can't silently reintroduce them.
 */
describe("Google ADK — API correctness regressions", () => {
  const allSnippets = () => {
    const d = getAdkData();
    return [
      d.quickstart,
      d.app.snippet,
      d.app.runnerSnippet,
      d.app.configSnippet,
      d.app.legacySnippet,
      d.a2a.snippet,
      ...d.primitives.map((p) => p.snippet),
    ].join("\n");
  };

  it("uses InMemorySessionService, never the non-existent InMemorySessionStore", () => {
    const text = allSnippets();
    expect(text).toContain("InMemorySessionService");
    expect(text).not.toContain("InMemorySessionStore");
  });

  it("constructs Runner with app= and session_service=, not agent= and session_store=", () => {
    const text = allSnippets();
    expect(text).toContain("Runner(app=app, session_service=session_service)");
    expect(text).not.toContain("session_store=");
  });

  it("calls run_async with user_id/session_id/new_message, not a positional session id", () => {
    const text = allSnippets();
    expect(text).toContain("new_message=types.Content(");
    expect(text).not.toContain("user_message=");
  });

  it("registers tools as plain functions — no fabricated @tool decorator", () => {
    const text = allSnippets();
    expect(text).toContain("tools=[");
    expect(text).not.toMatch(/^@tool$/m);
  });

  it("exposes the App container as a primitive", () => {
    const data = getAdkData();
    expect(data.primitives.some((p) => p.name === "App")).toBe(true);
  });
});

describe("Google ADK — App container", () => {
  it("carries fields, plugins, configs, legacy differences, and limitations", () => {
    const { app } = getAdkData();
    const fieldNames = app.fields.map((f) => f.field);
    expect(fieldNames).toEqual(
      expect.arrayContaining([
        "name",
        "root_agent",
        "plugins",
        "context_cache_config",
        "events_compaction_config",
        "resumability_config",
      ])
    );
    expect(app.plugins.some((p) => p.name === "LoggingPlugin")).toBe(true);
    const configNames = app.configs.map((c) => c.name);
    expect(configNames).toEqual(
      expect.arrayContaining([
        "ContextCacheConfig",
        "EventsCompactionConfig",
        "ResumabilityConfig",
      ])
    );
    // All three cross-cutting configs are experimental upstream.
    expect(app.configs.every((c) => c.experimental)).toBe(true);
    expect(app.legacyDifferences.length).toBeGreaterThanOrEqual(3);
    expect(app.limitations.length).toBeGreaterThanOrEqual(3);
    expect(app.nameRules).toMatch(/reserved/i);
  });

  it("pins EventsCompactionConfig to its real import path (not re-exported from google.adk.apps)", () => {
    const { app } = getAdkData();
    const compaction = app.configs.find((c) => c.name === "EventsCompactionConfig")!;
    expect(compaction.importPath).toBe("google.adk.apps.app");
  });
});

describe("Google ADK — A2A distributed topology", () => {
  it("names the five services and the agent-card path", () => {
    const { a2a } = getAdkData();
    const names = a2a.services.map((s) => s.name);
    expect(names).toEqual(
      expect.arrayContaining([
        "orchestrator",
        "researcher",
        "judge",
        "content_builder",
        "app",
      ])
    );
    expect(a2a.services.filter((s) => s.kind === "orchestrator")).toHaveLength(1);
    expect(a2a.agentCardPath).toBe("/a2a/agent/.well-known/agent.json");
    expect(a2a.snippet).toContain("RemoteA2aAgent");
    expect(a2a.envVars.every((e) => e.key.length > 0)).toBe(true);
    expect(a2a.sharedFiles.some((f) => f.file === "a2a_utils.py")).toBe(true);
  });

  it("panel renders the App and A2A sections", () => {
    render(<GoogleAdkPanel data={getAdkData()} />);
    expect(screen.getAllByText(/The App container/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/App versus a bare agent/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Agent-to-Agent \(distributed topology\)/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("LoggingPlugin").length).toBeGreaterThan(0);
    expect(screen.getAllByText("orchestrator").length).toBeGreaterThan(0);
  });
});

describe("Agent Gateway tab", () => {
  it("returns controls, deployment modes, MCP services, and deploy steps", async () => {
    const data = getGatewayData();
    const controlIds = data.controls.map((c) => c.id);
    expect(controlIds).toEqual(
      expect.arrayContaining([
        "iap-request-authz",
        "agent-identity",
        "model-armor",
        "agent-registry",
      ])
    );
    expect(data.modes).toHaveLength(2);
    expect(data.modes.some((m) => m.secure)).toBe(true);
    expect(data.mcpServices.map((s) => s.name)).toEqual(
      expect.arrayContaining([
        "legacy-dms",
        "corporate-email",
        "income-verification-api",
      ])
    );
    // Steps must be contiguous and ordered.
    const orders = data.steps.map((s) => s.order);
    expect(orders).toEqual([...orders].sort((a, b) => a - b));
    expect(data.sakthaiRelevance).toMatch(/GuardrailPolicy/);

    const res = await gatewayGet();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.gateway.controls.length).toBe(data.controls.length);
  });

  it("renders request path, controls, modes, and the sakthai mapping", () => {
    render(<AgentGatewayPanel data={getGatewayData()} />);
    expect(screen.getByText(/Governing Agentic Workloads/i)).toBeInTheDocument();
    expect(screen.getByText(/Request path/i)).toBeInTheDocument();
    expect(screen.getByText("Model Armor CONTENT_AUTHZ")).toBeInTheDocument();
    expect(screen.getByText(/How this maps onto sakthai/i)).toBeInTheDocument();
  });

  it("renders loading state when data is null", () => {
    render(<AgentGatewayPanel data={null} />);
    expect(screen.getByText(/Loading gateway inventory/i)).toBeInTheDocument();
  });
});

describe("Learning tab — staleness annotations", () => {
  it("includes the AI Platform qwik start lab flagged as pre-Vertex", () => {
    const data = getGcpLearningData();
    const lab = data.resources.find((r) => r.id === "ai-platform-qwik-start");
    expect(lab).toBeDefined();
    expect(lab!.description).toMatch(/Vertex AI supersedes|legacy AI Platform/i);
    expect(lab!.tags).toEqual(expect.arrayContaining(["notebooks"]));
  });

  it("exposes staleness notes naming the retired gcloud ai-platform surface", () => {
    expect(GCP_LEARNING_STALENESS_NOTES.length).toBeGreaterThan(0);
    expect(GCP_LEARNING_STALENESS_NOTES.join(" ")).toMatch(/gcloud ai-platform/);
  });
});
