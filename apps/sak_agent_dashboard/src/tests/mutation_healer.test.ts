import { describe, it, expect } from 'vitest';
import { SelfHealingTestGenerator } from '../lib/mutation/selfHealingTestGenerator';
import { MutantRecord } from '../lib/mutation/types';

describe('SelfHealingTestGenerator', () => {
  it('synthesizes a targeted vitest assertion to kill a surviving TypeScript mutant', () => {
    const mutant: MutantRecord = {
      id: 'mut-sample-1',
      sourceFile: 'src/lib/eval/evalEngine.ts',
      line: 85,
      originalSnippet: 'if (safetyCompliance === 0)',
      mutatedSnippet: 'if (safetyCompliance !== 0)',
      operator: 'conditional_inversion',
      status: 'survived',
      latencyMs: 12
    };

    const healResult = SelfHealingTestGenerator.synthesizeHealerTest(mutant);
    expect(healResult.verifiedKilled).toBe(true);
    expect(healResult.testFramework).toBe('vitest');
    expect(healResult.synthesizedTestCode).toContain("it('healer:");
    expect(healResult.synthesizedTestCode).toContain('expect(');
  });

  it('synthesizes a pytest test function for Python files', () => {
    const mutant: MutantRecord = {
      id: 'mut-sample-py',
      sourceFile: 'personas/sakthai/sakthai/agent/guardrails.py',
      line: 50,
      originalSnippet: 'return target_agent',
      mutatedSnippet: 'return None',
      operator: 'return_value_substitution',
      status: 'survived',
      latencyMs: 15
    };

    const healResult = SelfHealingTestGenerator.synthesizeHealerTest(mutant);
    expect(healResult.testFramework).toBe('pytest');
    expect(healResult.synthesizedTestCode).toContain('def test_healer_');
    expect(healResult.synthesizedTestCode).toContain('assert ');
  });

  it('batch synthesizes tests for a mutant list', () => {
    const mutants: MutantRecord[] = [
      {
        id: 'm1',
        sourceFile: 'a.ts',
        line: 1,
        originalSnippet: 'a >= b',
        mutatedSnippet: 'a < b',
        operator: 'conditional_inversion',
        status: 'survived',
        latencyMs: 5
      },
      {
        id: 'm2',
        sourceFile: 'b.ts',
        line: 2,
        originalSnippet: 'true',
        mutatedSnippet: 'false',
        operator: 'boolean_flip',
        status: 'killed',
        latencyMs: 5
      }
    ];

    const results = SelfHealingTestGenerator.batchHeal(mutants);
    expect(results).toHaveLength(1);
    expect(results[0].mutantId).toBe('m1');
  });
});
