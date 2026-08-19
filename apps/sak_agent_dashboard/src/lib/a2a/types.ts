/**
 * Agent-to-Agent (A2A) Protocol & Service Registry Domain Types.
 * Standardized JSON-RPC 2.0 framing, capability descriptors, health telemetry,
 * real-time chunk streaming, and consensus voting models for Sak-Family agents.
 */

export type ChunkType = "token" | "tool_call" | "tool_result" | "vote";
export type VoteChoice = "approve" | "reject" | "abstain" | "veto";

export interface A2AStreamChunk {
  seq: number;
  persona: string;
  turn: number;
  chunkType: ChunkType;
  delta: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
  stopReason?: string | null;
}

export interface A2AVoteBallot {
  sessionId: string;
  persona: string;
  choice: VoteChoice;
  weight: number;
  rationale?: string;
  timestamp: string;
}

export interface A2AConsensusSession {
  sessionId: string;
  topic: string;
  domain: "security" | "vision" | "content" | "devops" | "governance" | "general";
  quorumThreshold: number;
  resolved: boolean;
  outcome: "PENDING" | "APPROVED" | "REJECTED" | "VETOED";
  createdAt: string;
  ballots: A2AVoteBallot[];
}

export interface A2AMessageEnvelope<T = Record<string, unknown>> {
  jsonrpc: "2.0";
  id: string;
  agentFrom: string;
  agentTo: string;
  method: string;
  params: T;
  correlationId: string;
  timestamp: string;
  signature?: string;
}

export interface A2ACapabilityDescriptor {
  id: string;
  name: string;
  description: string;
  category: "coding" | "security" | "orchestration" | "analytics" | "memory" | "prompt";
  inputSchema: Record<string, unknown>;
  outputSchema: Record<string, unknown>;
  rateLimitRpm: number;
  avgLatencyMs: number;
  astRequired: boolean;
}

export interface A2AServiceRegistration {
  agentSlug: string;
  agentName: string;
  role: string;
  endpoint: string;
  capabilities: A2ACapabilityDescriptor[];
  healthStatus: "healthy" | "degraded" | "offline";
  lastHeartbeat: string;
  version: string;
  uptimeSeconds: number;
  totalCallsHandled: number;
}

export interface A2ADelegationRequest {
  agentFrom: string;
  agentTo: string;
  capabilityId: string;
  payload: Record<string, unknown>;
  timeoutMs?: number;
}

export interface A2ADelegationResult {
  delegationId: string;
  correlationId: string;
  agentFrom: string;
  agentTo: string;
  method: string;
  status: "success" | "failed" | "timeout";
  result?: unknown;
  error?: string;
  executionTimeMs: number;
  astAudited: boolean;
  timestamp: string;
}

export interface A2AHealthStatus {
  fleetSize: number;
  healthyNodes: number;
  totalCapabilities: number;
  uptimePercentage: number;
  avgFleetLatencyMs: number;
  activeDelegations: number;
}

/** Runtime Guard for A2AMessageEnvelope */
export function isValidA2AEnvelope(data: unknown): data is A2AMessageEnvelope {
  if (typeof data !== "object" || data === null) return false;
  const d = data as Record<string, unknown>;
  return (
    d.jsonrpc === "2.0" &&
    typeof d.id === "string" &&
    typeof d.agentFrom === "string" &&
    typeof d.agentTo === "string" &&
    typeof d.method === "string" &&
    typeof d.params === "object" &&
    typeof d.correlationId === "string"
  );
}

/** Runtime Guard for A2AServiceRegistration */
export function isValidServiceRegistration(data: unknown): data is A2AServiceRegistration {
  if (typeof data !== "object" || data === null) return false;
  const d = data as Record<string, unknown>;
  return (
    typeof d.agentSlug === "string" &&
    typeof d.agentName === "string" &&
    Array.isArray(d.capabilities) &&
    (d.healthStatus === "healthy" || d.healthStatus === "degraded" || d.healthStatus === "offline")
  );
}
