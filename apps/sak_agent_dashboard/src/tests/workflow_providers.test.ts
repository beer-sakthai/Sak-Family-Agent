import { describe, it, expect } from "vitest";
import { PROVIDERS, getProvider, resolveProviderForPersona } from "../lib/providers";
import {
  WORKFLOW_TOPOLOGIES,
  getWorkflows,
  getWorkflowById,
  executeWorkflow,
  validateWorkflowDAG,
  buildTopologicalBatches,
  interpolateState,
} from "../lib/workflowEngine";
import { GET as getProvidersRoute } from "../app/api/providers/route";
import { GET as getWorkflowRoute, POST as postWorkflowRoute } from "../app/api/workflow/route";
import { NextRequest } from "next/server";
import { WorkflowTopology } from "../lib/types";

describe("Multi-Provider AI Matrix & Specifications", () => {
  it("defines all major AI provider ecosystems including Microsoft M365", () => {
    expect(PROVIDERS.length).toBeGreaterThanOrEqual(6);
    const providerIds = PROVIDERS.map((p) => p.id);
    expect(providerIds).toContain("claude");
    expect(providerIds).toContain("codex");
    expect(providerIds).toContain("opencode");
    expect(providerIds).toContain("ollama");
    expect(providerIds).toContain("huggingface");
    expect(providerIds).toContain("gemini_agy");
    expect(providerIds).toContain("m365_azure");
  });

  it("ensures every provider contains valid models, pricing, and health specs", () => {
    for (const prov of PROVIDERS) {
      expect(prov.name).toBeTruthy();
      expect(prov.vendor).toBeTruthy();
      expect(prov.defaultModel).toBeTruthy();
      expect(prov.health).toBe("healthy");
      expect(prov.latencyMs).toBeGreaterThan(0);
      expect(prov.supportedModels.length).toBeGreaterThan(0);
      expect(prov.assignedPersonas.length).toBeGreaterThan(0);

      for (const model of prov.supportedModels) {
        expect(model.id).toBeTruthy();
        expect(model.name).toBeTruthy();
        expect(model.contextWindow).toBeGreaterThan(0);
        expect(model.inputCostPer1M).toBeGreaterThanOrEqual(0);
        expect(model.outputCostPer1M).toBeGreaterThanOrEqual(0);
        expect(model.capabilities.length).toBeGreaterThan(0);
      }
    }
  });

  it("resolves providers and fallback cascades for all 6 personas", () => {
    const personas = ["SakThai", "SakKing", "SakSee", "SakSit", "SakJules", "SakTan"];

    for (const p of personas) {
      const { primary, fallback } = resolveProviderForPersona(p);
      expect(primary).toBeDefined();
      expect(fallback).toBeDefined();
      expect(fallback.id).toBe("ollama");
    }
  });

  it("handles getProvider lookup correctly", () => {
    expect(getProvider("claude")?.name).toBe("Anthropic Claude");
    expect(getProvider("ollama")?.isLocal).toBe(true);
    expect(getProvider("gemini_agy")?.vendor).toBe("Google DeepMind");
  });
});

describe("6-Agent Workflow Framework & Orchestration Engine", () => {
  it("provides built-in topologies covering autonomous, security, and publishing cycles", () => {
    const topologies = getWorkflows();
    expect(topologies.length).toBeGreaterThanOrEqual(3);

    const fullCycle = getWorkflowById("full_cycle");
    expect(fullCycle).toBeDefined();
    expect(fullCycle?.stages).toHaveLength(6);

    const stagePersonas = fullCycle?.stages.map((s) => s.personaSlug);
    expect(stagePersonas).toEqual([
      "sakthai",
      "saksee",
      "saksit",
      "sakking",
      "sakjules",
      "saktan",
    ]);
  });

  it("simulates workflow execution and generates valid execution metrics", async () => {
    const result = await executeWorkflow("full_cycle");
    expect(result.executionId).toMatch(/^exec_/);
    expect(result.workflowId).toBe("full_cycle");
    expect(result.status).toBe("completed");
    expect(result.stages).toHaveLength(6);
    expect(result.totalTokens).toBeGreaterThan(0);
    expect(result.totalLatencyMs).toBeGreaterThan(0);

    for (const stage of result.stages) {
      expect(stage.status).toBe("completed");
      expect(stage.durationMs).toBeGreaterThan(0);
      expect(stage.tokensUsed).toBeGreaterThan(0);
      expect(stage.outputSummary).toBeTruthy();
    }
  });

  it("validates DAG topologies and detects cycles or missing dependencies", () => {
    const validTopology: WorkflowTopology = {
      id: "test_valid",
      name: "Valid Test",
      description: "DAG without cycles",
      category: "autonomous",
      stages: [
        {
          id: "step_a",
          name: "Step A",
          personaSlug: "sakthai",
          personaName: "SakThai",
          provider: "gemini_agy",
          model: "gemini-2.5-pro",
          action: "action A",
          status: "pending",
          dependsOn: [],
        },
        {
          id: "step_b",
          name: "Step B",
          personaSlug: "sakking",
          personaName: "SakKing",
          provider: "codex",
          model: "gpt-4o",
          action: "action B",
          status: "pending",
          dependsOn: ["step_a"],
        },
      ],
    };

    const validRes = validateWorkflowDAG(validTopology);
    expect(validRes.isValid).toBe(true);
    expect(validRes.topologicalOrder).toEqual(["step_a", "step_b"]);

    const batches = buildTopologicalBatches(validTopology);
    expect(batches).toHaveLength(2);
    expect(batches[0][0].id).toBe("step_a");
    expect(batches[1][0].id).toBe("step_b");

    // Cyclic Topology
    const cyclicTopology: WorkflowTopology = {
      id: "test_cyclic",
      name: "Cyclic Test",
      description: "DAG with cycles",
      category: "autonomous",
      stages: [
        {
          id: "c1",
          name: "C1",
          personaSlug: "sakthai",
          personaName: "SakThai",
          provider: "gemini_agy",
          model: "gemini-2.5-pro",
          action: "action 1",
          status: "pending",
          dependsOn: ["c2"],
        },
        {
          id: "c2",
          name: "C2",
          personaSlug: "sakking",
          personaName: "SakKing",
          provider: "codex",
          model: "gpt-4o",
          action: "action 2",
          status: "pending",
          dependsOn: ["c1"],
        },
      ],
    };

    const cyclicRes = validateWorkflowDAG(cyclicTopology);
    expect(cyclicRes.isValid).toBe(false);
    expect(cyclicRes.errors[0]).toContain("Cyclic dependency detected");
  });

  it("interpolates state variables accurately", () => {
    const state = {
      s1: { plan_id: "plan_999", count: 42 },
    };

    expect(interpolateState("${steps.s1.output.plan_id}", state)).toBe("plan_999");
    expect(interpolateState("${steps.s1.output.count}", state)).toBe(42);
    expect(interpolateState("The plan is ${steps.s1.output.plan_id}", state)).toBe("The plan is plan_999");
  });
});

describe("Backend API Route Handlers", () => {
  it("GET /api/providers returns all providers with success true", async () => {
    const res = await getProvidersRoute();
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.totalProviders).toBe(7);
    expect(data.providers).toHaveLength(7);
  });

  it("GET /api/workflow returns workflow topologies and handles ?id lookup", async () => {
    const listReq = new NextRequest("http://localhost:3000/api/workflow");
    const listRes = await getWorkflowRoute(listReq);
    expect(listRes.status).toBe(200);
    const listData = await listRes.json();
    expect(listData.success).toBe(true);
    expect(listData.workflows.length).toBeGreaterThanOrEqual(3);

    const detailReq = new NextRequest("http://localhost:3000/api/workflow?id=full_cycle");
    const detailRes = await getWorkflowRoute(detailReq);
    expect(detailRes.status).toBe(200);
    const detailData = await detailRes.json();
    expect(detailData.success).toBe(true);
    expect(detailData.workflow.id).toBe("full_cycle");
  });

  it("POST /api/workflow triggers execution and validates payload", async () => {
    const invalidReq = new NextRequest("http://localhost:3000/api/workflow", {
      method: "POST",
      body: JSON.stringify({}),
    });
    const invalidRes = await postWorkflowRoute(invalidReq);
    expect(invalidRes.status).toBe(400);

    const validReq = new NextRequest("http://localhost:3000/api/workflow", {
      method: "POST",
      body: JSON.stringify({ workflowId: "security_gate" }),
    });
    const validRes = await postWorkflowRoute(validReq);
    expect(validRes.status).toBe(200);
    const validData = await validRes.json();
    expect(validData.success).toBe(true);
    expect(validData.result.workflowId).toBe("security_gate");
    expect(validData.result.stages).toHaveLength(2);
  });
});
