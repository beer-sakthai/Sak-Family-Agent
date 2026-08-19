import { describe, it, expect } from 'vitest';
import { isValidMutantRecord, MutantRecord } from '../lib/mutation/types';

describe('Mutation Types Guard', () => {
  it('validates a valid MutantRecord structure', () => {
    const record: MutantRecord = {
      id: 'mut-1',
      sourceFile: 'src/lib/evalEngine.ts',
      line: 42,
      originalSnippet: 'if (score >= threshold)',
      mutatedSnippet: 'if (score < threshold)',
      operator: 'conditional_inversion',
      status: 'survived',
      latencyMs: 18,
    };
    expect(isValidMutantRecord(record)).toBe(true);
  });

  it('rejects invalid or incomplete records', () => {
    expect(isValidMutantRecord(null)).toBe(false);
    expect(isValidMutantRecord({ id: 'mut-1' })).toBe(false);
  });
});
