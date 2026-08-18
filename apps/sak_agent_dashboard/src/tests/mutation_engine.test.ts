import { describe, it, expect } from 'vitest';
import { MutationEngine } from '../lib/mutation/mutationEngine';

describe('MutationEngine', () => {
  it('generates AST mutants from code with conditional operators', () => {
    const code = `function isAllowed(score: number, threshold: number) {
      if (score >= threshold) {
        return true;
      }
      return false;
    }`;
    const mutants = MutationEngine.generateMutants('auth.ts', code);
    expect(mutants.length).toBeGreaterThanOrEqual(2);
    expect(mutants.some((m) => m.operator === 'conditional_inversion')).toBe(true);
    expect(mutants.some((m) => m.operator === 'boolean_flip')).toBe(true);
  });

  it('runs a simulated sweep and calculates mutation score', async () => {
    const summary = await MutationEngine.runSweep({
      targetFiles: ['src/lib/eval/evalEngine.ts'],
      operators: ['conditional_inversion', 'boolean_flip'],
      timeoutMs: 2000,
      concurrency: 2
    });
    expect(summary.totalMutants).toBeGreaterThan(0);
    expect(summary.mutationScorePercent).toBeGreaterThanOrEqual(0);
    expect(summary.sweepId).toContain('sweep-');
  });

  it('retrieves recent sweeps and mutants', () => {
    const sweeps = MutationEngine.getRecentSweeps();
    expect(sweeps.length).toBeGreaterThanOrEqual(1);

    const mutants = MutationEngine.getMutants();
    expect(mutants.length).toBeGreaterThanOrEqual(1);
  });
});
