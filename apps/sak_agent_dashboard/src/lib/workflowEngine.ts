import {
  WorkflowTopology,
  WorkflowExecutionResult,
  WorkflowStage,
  DAGValidationResult,
  WorkflowRunHistory,
} from "./types";
import { telemetryBus } from "./telemetryBus";
import { randomBytes } from "crypto";

export const WORKFLOW_TOPOLOGIES: WorkflowTopology[] = [
  {
    id: "full_cycle",
    name: "Full 6-Agent Autonomous Feature Cycle",
    description:
      "End-to-end specification, research, drafting, security hardening, automated CI/CD PR, and journal logging.",
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
        dependsOn: [],
        retry: 1,
        retryDelay: 0.1,
        params: { mode: "architect", depth: "full" },
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
        dependsOn: ["stage_1_plan"],
        params: { upstream: "specs", target: "${steps.stage_1_plan.output.plan_id}" },
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
        dependsOn: ["stage_2_scout"],
        params: { context: "${steps.stage_2_scout.output.assets}" },
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
        dependsOn: ["stage_3_draft"],
        params: { strict: true, sandbox: "hermetic" },
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
        dependsOn: ["stage_4_audit"],
        retry: 2,
        retryDelay: 0.2,
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
        dependsOn: ["stage_5_cicd"],
      },
    ],
  },
  {
    id: "parallel_cycle",
    name: "Parallel Fan-Out/Fan-In Multi-Agent DAG",
    description:
      "Parallel task dispatching where research and static analysis run concurrently before synthesis.",
    category: "autonomous",
    stages: [
      {
        id: "fanout_root",
        name: "Task Partitioning & Spec Generation",
        personaSlug: "sakthai",
        personaName: "SakThai",
        provider: "gemini_agy",
        model: "gemini-2.5-pro",
        action: "Decompose feature into independent work items",
        status: "pending",
        dependsOn: [],
      },
      {
        id: "branch_scout",
        name: "External Intelligence Gathering",
        personaSlug: "saksee",
        personaName: "SakSee",
        provider: "huggingface",
        model: "gemini-2.5-flash-lite",
        action: "Crawl documentation and gather reference benchmarks",
        status: "pending",
        dependsOn: ["fanout_root"],
      },
      {
        id: "branch_security",
        name: "Vulnerability & Threat Modeling",
        personaSlug: "sakking",
        personaName: "SakKing",
        provider: "codex",
        model: "o3-mini",
        action: "Run pre-emptive static security heuristics",
        status: "pending",
        dependsOn: ["fanout_root"],
      },
      {
        id: "fanin_join",
        name: "Unified Synthesis & PR Generation",
        personaSlug: "sakjules",
        personaName: "SakJules",
        provider: "gemini_agy",
        model: "gemini-2.5-flash",
        action: "Join parallel streams, run full test suite, and open PR",
        status: "pending",
        dependsOn: ["branch_scout", "branch_security"],
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
        dependsOn: [],
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
        dependsOn: ["sec_1_scan"],
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
        dependsOn: [],
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
        dependsOn: ["hf_1_audit"],
      },
    ],
  },
];

// In-memory run history cache
const runHistoryStore: Map<string, WorkflowRunHistory> = new Map();

/**
 * Validates a workflow topology DAG:
 * - Unique step IDs
 * - Valid dependencies
 * - Absence of cyclic dependencies
 * - Returns topological execution order
 */
export function validateWorkflowDAG(topology: WorkflowTopology): DAGValidationResult {
  const errors: string[] = [];
  const stages = topology.stages || [];

  if (stages.length === 0) {
    return {
      isValid: false,
      errors: ["Workflow must contain at least one stage."],
    };
  }

  const stageIds = new Set<string>();
  for (const s of stages) {
    if (!s.id || typeof s.id !== "string") {
      errors.push("Every stage must possess a non-empty string ID.");
      continue;
    }
    if (stageIds.has(s.id)) {
      errors.push(`Duplicate stage ID detected: '${s.id}'`);
    }
    stageIds.add(s.id);
  }

  // Check dependencies exist
  for (const s of stages) {
    const deps = s.dependsOn || [];
    for (const dep of deps) {
      if (!stageIds.has(dep)) {
        errors.push(`Stage '${s.id}' depends on non-existent stage '${dep}'.`);
      }
      if (dep === s.id) {
        errors.push(`Stage '${s.id}' cannot depend on itself (self-cycle).`);
      }
    }
  }

  if (errors.length > 0) {
    return { isValid: false, errors };
  }

  // Kahn's algorithm for cycle detection and topological sorting
  const inDegree = new Map<string, number>();
  const adj = new Map<string, string[]>();

  for (const s of stages) {
    inDegree.set(s.id, 0);
    adj.set(s.id, []);
  }

  for (const s of stages) {
    const deps = s.dependsOn || [];
    inDegree.set(s.id, deps.length);
    for (const dep of deps) {
      adj.get(dep)?.push(s.id);
    }
  }

  const queue: string[] = [];
  for (const [id, deg] of inDegree.entries()) {
    if (deg === 0) {
      queue.push(id);
    }
  }

  const topologicalOrder: string[] = [];
  while (queue.length > 0) {
    const current = queue.shift()!;
    topologicalOrder.push(current);

    const neighbors = adj.get(current) || [];
    for (const next of neighbors) {
      const newDeg = (inDegree.get(next) || 1) - 1;
      inDegree.set(next, newDeg);
      if (newDeg === 0) {
        queue.push(next);
      }
    }
  }

  if (topologicalOrder.length !== stages.length) {
    const remainingCycleNodes = stages
      .filter((s) => !topologicalOrder.includes(s.id))
      .map((s) => s.id);
    errors.push(
      `Cyclic dependency detected in workflow DAG involving stages: ${remainingCycleNodes.join(", ")}`
    );
    return { isValid: false, errors };
  }

  return {
    isValid: true,
    errors: [],
    topologicalOrder,
  };
}

/**
 * Builds topological batches of stages that can execute in parallel.
 */
export function buildTopologicalBatches(topology: WorkflowTopology): WorkflowStage[][] {
  const validation = validateWorkflowDAG(topology);
  if (!validation.isValid) {
    throw new Error(`Cannot build batches from invalid DAG: ${validation.errors.join("; ")}`);
  }

  const stageMap = new Map<string, WorkflowStage>();
  for (const s of topology.stages) {
    stageMap.set(s.id, s);
  }

  const inDegree = new Map<string, number>();
  const adj = new Map<string, string[]>();

  for (const s of topology.stages) {
    inDegree.set(s.id, (s.dependsOn || []).length);
    adj.set(s.id, []);
  }

  for (const s of topology.stages) {
    for (const dep of s.dependsOn || []) {
      adj.get(dep)?.push(s.id);
    }
  }

  const batches: WorkflowStage[][] = [];
  let available = topology.stages
    .filter((s) => (inDegree.get(s.id) || 0) === 0)
    .map((s) => s.id);

  while (available.length > 0) {
    const currentBatch = available.map((id) => stageMap.get(id)!);
    batches.push(currentBatch);

    const nextAvailable: string[] = [];
    for (const id of available) {
      for (const next of adj.get(id) || []) {
        const remaining = (inDegree.get(next) || 1) - 1;
        inDegree.set(next, remaining);
        if (remaining === 0) {
          nextAvailable.push(next);
        }
      }
    }
    available = nextAvailable;
  }

  return batches;
}

/**
 * Interpolates state references in parameters matching ${steps.<step_id>.output.<key>}.
 */
export function interpolateState(expression: any, stateContext: Record<string, any>): any {
  if (typeof expression !== "string") {
    if (Array.isArray(expression)) {
      return expression.map((item) => interpolateState(item, stateContext));
    }
    if (expression && typeof expression === "object") {
      const res: Record<string, any> = {};
      for (const [k, v] of Object.entries(expression)) {
        res[k] = interpolateState(v, stateContext);
      }
      return res;
    }
    return expression;
  }

  // Exact single expression: "${steps.step_1.output.value}"
  const exactMatch = expression.match(/^\$\{steps\.([a-zA-Z0-9_-]+)\.output\.([a-zA-Z0-9_.-]+)\}$/);
  if (exactMatch) {
    const [, stepId, outputKey] = exactMatch;
    const stepOutput = stateContext[stepId];
    if (stepOutput && outputKey in stepOutput) {
      return stepOutput[outputKey];
    }
    return expression;
  }

  // Inlined expressions: "Prefix ${steps.s1.output.id} suffix"
  return expression.replace(
    /\$\{steps\.([a-zA-Z0-9_-]+)\.output\.([a-zA-Z0-9_.-]+)\}/g,
    (match, stepId, outputKey) => {
      const stepOutput = stateContext[stepId];
      if (stepOutput && outputKey in stepOutput) {
        return String(stepOutput[outputKey]);
      }
      return match;
    }
  );
}

export function getWorkflows(): WorkflowTopology[] {
  return WORKFLOW_TOPOLOGIES.map((wf) => ({
    ...wf,
    validation: validateWorkflowDAG(wf),
  }));
}

export function getWorkflowById(id: string): WorkflowTopology | undefined {
  const found = WORKFLOW_TOPOLOGIES.find((w) => w.id === id);
  if (!found) return undefined;
  return {
    ...found,
    validation: validateWorkflowDAG(found),
  };
}

export function getRunHistories(): WorkflowRunHistory[] {
  return Array.from(runHistoryStore.values());
}

export function getRunHistoryById(runId: string): WorkflowRunHistory | undefined {
  return runHistoryStore.get(runId);
}

/**
 * Execute a multi-agent workflow pipeline following its topological DAG stages,
 * resolving dependencies, interpolating state outputs, and broadcasting real-time telemetry events.
 */
export async function executeWorkflow(
  workflowId: string,
  customTopology?: WorkflowTopology,
  inputParams: Record<string, any> = {}
): Promise<WorkflowExecutionResult> {
  const topology = customTopology || getWorkflowById(workflowId) || WORKFLOW_TOPOLOGIES[0];
  const validation = validateWorkflowDAG(topology);

  if (!validation.isValid) {
    throw new Error(`Invalid workflow DAG: ${validation.errors.join("; ")}`);
  }

  const executionId = `exec_${Date.now()}_${randomBytes(4).toString("hex")}`;
  const startTime = new Date().toISOString();
  const stateContext: Record<string, Record<string, any>> = { ...inputParams };
  const stageResults: Map<string, WorkflowStage> = new Map();

  const batches = buildTopologicalBatches(topology);

  for (const batch of batches) {
    // Process parallel stages in batch
    await Promise.all(
      batch.map(async (stage) => {
        const stageStart = new Date().toISOString();
        const resolvedParams = interpolateState(stage.params || {}, stateContext);

        const durationMs = Math.floor(Math.random() * 250) + 120;
        const tokensUsed = Math.floor(Math.random() * 450) + 150;

        // Simulated structured output for downstream DAG consumption
        const stageOutput: Record<string, any> = {
          [`${stage.id}_status`]: "OK",
          plan_id: `plan_${stage.id}_${Date.now().toString(36)}`,
          assets: `artifacts/${stage.personaSlug}/${stage.id}.json`,
          verified: true,
          timestamp: stageStart,
          resolvedParams,
        };

        stateContext[stage.id] = stageOutput;

        const updatedStage: WorkflowStage = {
          ...stage,
          status: "completed",
          durationMs,
          tokensUsed,
          params: resolvedParams,
          output: stageOutput,
          outputSummary: `Executed ${stage.action} successfully using ${stage.model}`,
          startTime: stageStart,
          endTime: new Date().toISOString(),
          attempts: 1,
        };

        stageResults.set(stage.id, updatedStage);

        // Emit live stage telemetry
        telemetryBus.emitEvent({
          type: "agent_message",
          persona: stage.personaName,
          sessionId: executionId,
          data: {
            message: `Stage '${stage.name}' finished [${stage.provider}/${stage.model}] (+${tokensUsed} tok, ${durationMs}ms)`,
            stageId: stage.id,
            status: "completed",
          },
        });
      })
    );
  }

  const activeStages = topology.stages.map((s) => stageResults.get(s.id)!);
  const totalTokens = activeStages.reduce((acc, s) => acc + (s.tokensUsed || 0), 0);
  const totalLatencyMs = activeStages.reduce((acc, s) => acc + (s.durationMs || 0), 0);
  const endTime = new Date().toISOString();

  const historyRecord: WorkflowRunHistory = {
    runId: executionId,
    workflowId: topology.id,
    workflowName: topology.name,
    status: "completed",
    startTime,
    endTime,
    stages: activeStages,
    totalTokens,
    totalLatencyMs,
  };

  runHistoryStore.set(executionId, historyRecord);

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
    endTime,
    stages: activeStages,
    totalTokens,
    totalLatencyMs,
    dagTopologicalOrder: validation.topologicalOrder,
    history: historyRecord,
  };
}
