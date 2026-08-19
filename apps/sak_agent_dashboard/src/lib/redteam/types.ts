/**
 * Domain types for Autonomous Red-Teaming & Adversarial Jailbreak Fuzzing.
 */

export type AttackVector =
  | 'recursive_prompt_injection'
  | 'cipher_encoding'
  | 'dan_persona_override'
  | 'ast_guardrail_evasion'
  | 'context_leak_exfiltration'
  | 'polyglot_payload';

export type AttackSeverity = 'critical' | 'high' | 'medium' | 'low';

export interface FuzzingPayload {
  payloadId: string;
  vector: AttackVector;
  title: string;
  rawPayload: string;
  encodedPayload?: string;
  encodingType?: 'plain' | 'base64' | 'rot13' | 'unicode_homoglyph' | 'hex';
  severity: AttackSeverity;
  targetPersona: string;
  expectedOutcome: 'blocked' | 'sanitized';
}

export interface FuzzingVerdict {
  verdictId: string;
  payloadId: string;
  vector: AttackVector;
  status: 'BLOCKED' | 'EVADED' | 'MITIGATED';
  robustnessScore: number; // 0 to 100
  defenseTechnique: string;
  matchedRule?: string;
  extractedThreatSnippet?: string;
  latencyMs: number;
  timestamp: string;
}

export interface RedTeamFuzzSummary {
  sweepId: string;
  totalPayloads: number;
  blockedCount: number;
  evadedCount: number;
  mitigatedCount: number;
  fleetRobustnessScore: number; // %
  durationMs: number;
  timestamp: string;
  vectorBreakdown: Record<AttackVector, { total: number; blocked: number; score: number }>;
}

export interface RedTeamSweepConfig {
  targetPersonas: string[];
  vectors: AttackVector[];
  payloadCount: number;
  mutationFuzzing: boolean;
}
