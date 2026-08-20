import { describe, it, expect } from 'vitest';
import { RedTeamEngine } from '../lib/redteam/redTeamEngine';

describe('RedTeamEngine', () => {
  it('generates adversarial fuzzing payloads across diverse attack vectors', () => {
    const payloads = RedTeamEngine.generateAdversarialPayloads();
    expect(payloads.length).toBeGreaterThanOrEqual(5);

    const vectors = payloads.map((p) => p.vector);
    expect(vectors).toContain('recursive_prompt_injection');
    expect(vectors).toContain('cipher_encoding');
    expect(vectors).toContain('dan_persona_override');
    expect(vectors).toContain('ast_guardrail_evasion');
  });

  it('correctly intercepts and blocks path traversal and injection payloads', () => {
    const payloads = RedTeamEngine.generateAdversarialPayloads();
    const traversalPayload = payloads.find((p) => p.vector === 'ast_guardrail_evasion')!;

    const verdict = RedTeamEngine.evaluatePayloadDefense(traversalPayload);
    expect(verdict.status).toBe('BLOCKED');
    expect(verdict.robustnessScore).toBe(100);
    expect(verdict.matchedRule).toBe('RULE_FORBIDDEN_PATH_TRAVERSAL');
  });

  it('runs a full fuzzing sweep and computes fleet robustness score', async () => {
    const summary = await RedTeamEngine.runFuzzSweep({
      targetPersonas: ['saksee'],
    });

    expect(summary.totalPayloads).toBeGreaterThanOrEqual(5);
    expect(summary.blockedCount).toBeGreaterThanOrEqual(4);
    expect(summary.fleetRobustnessScore).toBeGreaterThanOrEqual(90);
    expect(summary.sweepId).toContain('sweep-redteam-');
  });
});
