# Automated Mutation Testing & Self-Healing CI/CD Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-grade AST-driven Mutation Testing engine and Autonomous Self-Healing Test Synthesizer for the Sak-Family platform with an interactive dashboard studio and GitHub Actions CI quality gate.

**Architecture:** The subsystem analyzes source code files across TypeScript and Python, injects deterministic AST mutations (conditional flips, boolean swaps, boundary shifts, return value replacements), runs targeted test suites to calculate the Mutation Score ($\frac{\text{Killed}}{\text{Total}}$), and uses an autonomous self-healing generator to synthesize missing test assertions that kill surviving mutants.

**Tech Stack:** TypeScript, Next.js 16 (App Router), Vitest, React 19, Tailwind CSS, Lucide React, Pytest/Python 3.11 AST tooling.

**Spec:** [`docs/designs/mutation_testing_self_healing_spec.md`](file:///home/beern/Sak-Family-Agent/docs/designs/mutation_testing_self_healing_spec.md)

## Global Constraints

- Monorepo paths: Next.js dashboard at `apps/sak_agent_dashboard/`, core Python package at `personas/sakthai/sakthai/`.
- Strict TypeScript: `pnpm tsc --noEmit` must exit 0 with zero type errors.
- Target Mutation Score threshold: $\ge 85\%$ across core Seams.
- Security Invariant: AST Security Sentinel must audit all generated healer test fixtures before execution.

---

### Task 1: Mutation Domain Types & Schema Guards

**Files:**
- Create: `apps/sak_agent_dashboard/src/lib/mutation/types.ts`
- Modify: `apps/sak_agent_dashboard/src/lib/types.ts`
- Test: `apps/sak_agent_dashboard/src/tests/mutation_types.test.ts`

**Interfaces:**
- Produces: `MutationOperator`, `MutantRecord`, `MutationSweepConfig`, `MutationSweepSummary`, `HealPlanResult`, `isValidMutantRecord()`

- [ ] **Step 1: Write the failing test**

```typescript
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
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm vitest run src/tests/mutation_types.test.ts`
Expected: FAIL with module not found

- [ ] **Step 3: Write minimal implementation**

```typescript
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

export function isValidMutantRecord(data: unknown): data is MutantRecord {
  if (typeof data !== 'object' || data === null) return false;
  const d = data as Record<string, unknown>;
  return (
    typeof d.id === 'string' &&
    typeof d.sourceFile === 'string' &&
    typeof d.line === 'number' &&
    typeof d.originalSnippet === 'string' &&
    typeof d.mutatedSnippet === 'string'
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm vitest run src/tests/mutation_types.test.ts`
Expected: PASS

---

### Task 2: AST Mutation Engine & Fault Injector

**Files:**
- Create: `apps/sak_agent_dashboard/src/lib/mutation/mutationEngine.ts`
- Test: `apps/sak_agent_dashboard/src/tests/mutation_engine.test.ts`

**Interfaces:**
- Consumes: `MutationOperator`, `MutantRecord`, `MutationSweepSummary` from Task 1
- Produces: `MutationEngine.generateMutants()`, `MutationEngine.runSweep()`, `MutationEngine.getRecentSweeps()`

- [ ] **Step 1: Write the failing test**

```typescript
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
      concurrency: 2,
    });
    expect(summary.totalMutants).toBeGreaterThan(0);
    expect(summary.mutationScorePercent).toBeGreaterThanOrEqual(0);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm vitest run src/tests/mutation_engine.test.ts`
Expected: FAIL

- [ ] **Step 3: Write implementation**

Implement `MutationEngine` with AST regex tokenizer and operator substitution tables.

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm vitest run src/tests/mutation_engine.test.ts`
Expected: PASS

---

### Task 3: Autonomous Self-Healing Test Synthesizer

**Files:**
- Create: `apps/sak_agent_dashboard/src/lib/mutation/selfHealingTestGenerator.ts`
- Test: `apps/sak_agent_dashboard/src/tests/mutation_healer.test.ts`

**Interfaces:**
- Consumes: `MutantRecord` from Task 1
- Produces: `SelfHealingTestGenerator.synthesizeHealerTest(mutant: MutantRecord): HealPlanResult`

- [ ] **Step 1: Write the failing test**

```typescript
import { describe, it, expect } from 'vitest';
import { SelfHealingTestGenerator } from '../lib/mutation/selfHealingTestGenerator';
import { MutantRecord } from '../lib/mutation/types';

describe('SelfHealingTestGenerator', () => {
  it('synthesizes a targeted vitest assertion to kill a surviving mutant', () => {
    const mutant: MutantRecord = {
      id: 'mut-sample-1',
      sourceFile: 'src/lib/eval/evalEngine.ts',
      line: 85,
      originalSnippet: 'if (safetyCompliance === 0)',
      mutatedSnippet: 'if (safetyCompliance !== 0)',
      operator: 'conditional_inversion',
      status: 'survived',
      latencyMs: 12,
    };

    const healResult = SelfHealingTestGenerator.synthesizeHealerTest(mutant);
    expect(healResult.verifiedKilled).toBe(true);
    expect(healResult.synthesizedTestCode).toContain('it(');
    expect(healResult.synthesizedTestCode).toContain('expect(');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm vitest run src/tests/mutation_healer.test.ts`
Expected: FAIL

- [ ] **Step 3: Write implementation**

Implement rule-based and template-based test synthesizer for conditional inversions, boundary conditions, and null-returns.

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm vitest run src/tests/mutation_healer.test.ts`
Expected: PASS

---

### Task 4: REST API Route (`/api/mutation`)

**Files:**
- Create: `apps/sak_agent_dashboard/src/app/api/mutation/route.ts`
- Test: `apps/sak_agent_dashboard/src/tests/mutation_api.test.ts`

**Interfaces:**
- Consumes: `MutationEngine` and `SelfHealingTestGenerator`
- Produces: `GET /api/mutation` and `POST /api/mutation` (actions: `sweep`, `heal`, `list`)

- [ ] **Step 1: Write failing API route test**
- [ ] **Step 2: Verify test fails**
- [ ] **Step 3: Implement route handler in `src/app/api/mutation/route.ts`**
- [ ] **Step 4: Verify test passes**

---

### Task 5: Interactive Mutation Studio UI Panel & Dashboard Integration

**Files:**
- Create: `apps/sak_agent_dashboard/src/components/mutation/MutationStudioPanel.tsx`
- Modify: `apps/sak_agent_dashboard/src/app/page.tsx`
- Test: `apps/sak_agent_dashboard/src/tests/mutation_components.test.tsx`

**Features:**
- Mutation score radial gauge, killed/survived mutant ledger, AST diff inspector, 1-click test auto-healer button.
- Wired into navigation tab **🧬 Mutation Studio** in `src/app/page.tsx`.

- [ ] **Step 1: Write component test for `MutationStudioPanel`**
- [ ] **Step 2: Verify test fails**
- [ ] **Step 3: Implement `MutationStudioPanel.tsx` and wire tab in `src/app/page.tsx`**
- [ ] **Step 4: Verify test passes**

---

### Task 6: Monorepo CI Quality Gate & Full Verification

**Files:**
- Create: `Sak-Family-Agent/.github/workflows/mutation-self-healing-gate.yml`
- Create: `apps/sak_agent_dashboard/scripts/run_mutation_gate.sh`

- [ ] **Step 1: Write GitHub Actions workflow running mutation sweeps**
- [ ] **Step 2: Run all vitest test suites across the monorepo**
- [ ] **Step 3: Run `pnpm tsc --noEmit` and confirm 0 type errors**
- [ ] **Step 4: Run `pnpm run build` and confirm exit code 0**
