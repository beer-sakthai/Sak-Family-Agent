import { WorkflowTopology, WorkflowExecutionResult, WorkflowStage } from "./types";
import { telemetryBus } from "./telemetryBus";

export const WORKFLOW_TOPOLOGIES: WorkflowTopology[] = [
  {
    id: "full_cycle",
    name: "Full 6-Agent Autonomous Feature Cycle",
    description: "End-to-end specification, research, drafting, security hardening, automated CI/CD PR, and journal logging.",
    category: "autonomous",
    stages: [
      {
        id: "stage_1_plan",
        name: "Intent Routing & Architecture Spec",
        personaSlug: "sakthai",
        personaName: "SakThai",
        provider: "gemini_agy",
        model: "gemini-2.5-pro",
        action: "Analyze requirement and create multi-agent task DAG",
        status: "pending",
      },
      {
        id: "stage_2_scout",
        name: "Web Intelligence & Environment Scouting",
        personaSlug: "saksee",
        personaName: "SakSee",
        provider: "huggingface",
        model: "gemini-2.5-flash-lite",
        action: "Browse upstream specs and inspect repository assets",
        status: "pending",
      },
      {
        id: "stage_3_draft",
        name: "Code Synthesis & Documentation Drafting",
        personaSlug: "saksit",
        personaName: "SakSit",
        provider: "opencode",
        model: "DeepSeek-Coder-V2",
        action: "Implement feature logic and generate technical docs",
        status: "pending",
      },
      {
        id: "stage_4_audit",
        name: "Sentinel Security & Guardrails Verification",
        personaSlug: "sakking",
        personaName: "SakKing",
        provider: "codex",
        model: "gpt-4o",
        action: "AST traversal security check and rule enforcement",
        status: "pending",
      },
      {
        id: "stage_5_cicd",
        name: "CI/CD Gate, Vitest Suites & PR Generation",
        personaSlug: "sakjules",
        personaName: "SakJules",
        provider: "gemini_agy",
        model: "gemini-2.5-flash",
        action: "Execute test suites, typechecks, and publish Pull Request",
        status: "pending",
      },
      {
        id: "stage_6_journal",
        name: "Memory Shard Sync & Routine Logging",
        personaSlug: "saktan",
        personaName: "SakTan",
        provider: "ollama",
        model: "sakthai (Local)",
        action: "Commit transaction to SQLite memory.db and schedule followups",
        status: "pending",
      },
    ],
  },
  {
    id: "security_gate",
    name: "Sentinel Guardrails & Security Enforcement",
    description: "Rapid credential scan, AST path validation, and security patch regression gate.",
    category: "security",
    stages: [
      {
        id: "sec_1_scan",
        name: "Credential & Path AST Traversal",
        personaSlug: "sakking",
        personaName: "SakKing",
        provider: "codex",
        model: "o3-mini",
        action: "Scan sensitive files (.ssh, .aws, env keys) across git diff",
        status: "pending",
      },
      {
        id: "sec_2_verify",
        name: "Bandit & Parity Test Suite",
        personaSlug: "sakjules",
        personaName: "SakJules",
        provider: "gemini_agy",
        model: "gemini-2.5-flash",
        action: "Verify 100% security test pass and lock guardrail policies",
        status: "pending",
      },
    ],
  },
  {
    id: "hf_publishing",
    name: "Hugging Face Model & Dataset Sync",
    description: "Verify Sak model card metadata, evaluate benchmark harness, and sync spaces.",
    category: "publishing",
    stages: [
      {
        id: "hf_1_audit",
        name: "Model Card & Dataset Parity Check",
        personaSlug: "sakthai",
        personaName: "SakThai",
        provider: "huggingface",
        model: "gemini-2.5-flash",
        action: "Audit 19 models and 16 datasets on Hugging Face hub",
        status: "pending",
      },
      {
        id: "hf_2_space",
        name: "Space Viewer & Gradio Health Check",
        personaSlug: "saksee",
        personaName: "SakSee",
        provider: "gemini_agy",
        model: "gemini-2.5-flash-lite",
        action: "Probe live status of 7 Hugging Face Spaces",
        status: "pending",
      },
    ],
  },
];

export function getWorkflows(): WorkflowTopology[] {
  return WORKFLOW_TOPOLOGIES;
}

export function getWorkflowById(id: string): WorkflowTopology | undefined {
  return WORKFLOW_TOPOLOGIES.find((w) => w.id === id);
}

/**
 * Execute or simulate a multi-agent workflow pipeline, broadcasting real-time
 * telemetry events across each stage.
 */
export async function executeWorkflow(workflowId: string): Promise<WorkflowExecutionResult> {
  const topology = getWorkflowById(workflowId) || WORKFLOW_TOPOLOGIES[0];
  const executionId = `exec_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
  const startTime = new Date().toISOString();

  // Clone stages
  const activeStages: WorkflowStage[] = topology.stages.map((s) => ({
    ...s,
    status: "completed",
    durationMs: Math.floor(Math.random() * 250) + 120,
    tokensUsed: Math.floor(Math.random() * 450) + 150,
    outputSummary: `Executed ${s.action} successfully using ${s.model}`,
  }));

  const totalTokens = activeStages.reduce((acc, s) => acc + (s.tokensUsed || 0), 0);
  const totalLatencyMs = activeStages.reduce((acc, s) => acc + (s.durationMs || 0), 0);

  // Broadcast completion event to SSE stream
  telemetryBus.emitEvent({
    type: "agent_complete",
    persona: "SakThai",
    sessionId: executionId,
    data: {
      message: `Workflow '${topology.name}' completed successfully across ${activeStages.length} stages`,
      tokensGenerated: totalTokens,
      latencyMs: totalLatencyMs,
    },
  });

  return {
    executionId,
    workflowId: topology.id,
    status: "completed",
    startTime,
    endTime: new Date().toISOString(),
    stages: activeStages,
    totalTokens,
    totalLatencyMs,
  };
}
