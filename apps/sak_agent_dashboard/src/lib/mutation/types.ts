/**
 * Domain types and schema guards for the Automated Mutation Testing & Self-Healing CI/CD subsystem.
 */

export type MutationOperator =
  | 'conditional_inversion'
  | 'boolean_flip'
  | 'arithmetic_boundary'
  | 'return_value_substitution'
  | 'ast_node_strip';

export interface MutantRecord {
  id: string;
  sourceFile: string;
  line: number;
  originalSnippet: string;
  mutatedSnippet: string;
  operator: MutationOperator;
  status: 'killed' | 'survived' | 'timeout' | 'error';
  killingTestName?: string;
  latencyMs: number;
}

export interface MutationSweepConfig {
  targetFiles: string[];
  operators: MutationOperator[];
  timeoutMs: number;
  concurrency: number;
}

export interface MutationSweepSummary {
  sweepId: string;
  targetPackage: 'dashboard' | 'sakthai_core';
  totalMutants: number;
  killedMutants: number;
  survivedMutants: number;
  mutationScorePercent: number;
  healedMutantsCount: number;
  durationMs: number;
  timestamp: string;
}

export interface HealPlanResult {
  mutantId: string;
  sourceFile: string;
  diagnosedBlindspot: string;
  synthesizedTestCode: string;
  testFramework: 'vitest' | 'pytest';
  verifiedKilled: boolean;
}

/** Runtime Guard for MutantRecord */
export function isValidMutantRecord(data: unknown): data is MutantRecord {
  if (typeof data !== 'object' || data === null) return false;
  const d = data as Record<string, unknown>;
  return (
    typeof d.id === 'string' &&
    typeof d.sourceFile === 'string' &&
    typeof d.line === 'number' &&
    typeof d.originalSnippet === 'string' &&
    typeof d.mutatedSnippet === 'string' &&
    typeof d.operator === 'string' &&
    (d.status === 'killed' || d.status === 'survived' || d.status === 'timeout' || d.status === 'error')
  );
}
