# Sak-Agent-Family Dashboard — Test Infrastructure & Strategy Plan

## Executive Summary
This document establishes the official test infrastructure and opaque-box testing strategy for the **Sak-Agent-Family Dashboard**, an analytics and UI system built on Next.js 14/15 TypeScript.

The test strategy validates compliance with `ORIGINAL_REQUEST.md` and `PROJECT.md` without relying on private implementation details. All tests execute via `npm test` using **Vitest**, **React Testing Library**, and **JSDOM**.

---

## 1. Test Framework Setup & Environment

- **Framework**: Vitest `^2.1.3`
- **DOM Environment**: JSDOM `^25.0.1` + `@testing-library/react` `^16.0.1` + `@testing-library/jest-dom` `^6.6.2`
- **Path Aliases**: `@/*` maps to `./src/*`
- **Execution Command**: `npm test` (Runs `vitest run` non-interactively with 100% exit code check)
- **Configuration**:
  - `vitest.config.ts`: Defines `environment: 'jsdom'`, `globals: true`, setup file `./vitest.setup.ts`, alias resolution `@/ -> ./src/`.
  - `vitest.setup.ts`: Imports `@testing-library/jest-dom` matchers.

---

## 2. 4-Tier Test Suite Architecture

### Tier 1: Feature Coverage (Core API Endpoints & Components)
Focuses on standard functionality (happy path) defined in `PROJECT.md § Interface Contracts`:
1. **`/api/agents`**: Returns list of Sak-Agent-Family personas (`SakThai`, `SakKing`, `SakSee`, `SakSit`, `SakJules`) with valid status, role, model, and telemetry metrics.
2. **`/api/metrics`**: Returns aggregated performance stats (`totalRuns`, `avgLatencyMs`, `successRate`, `tokenStats`, `stopReasons`, `trends`).
3. **`/api/memory`**: Serves persistent agent memory records (`facts`, `observations`) and security `auditLogs`.
4. **`/api/sessions`**: Serves session transcript metadata (`sessions`, `total` count).
5. **Component Rendering**:
   - `AgentOverview`: Renders 5 persona cards with active status, badges, and latency metrics.
   - `AnalyticsCharts`: Renders visualizations for benchmark scores, token consumption, and stop reasons.
   - `SessionExplorer`: Renders searchable transcript list with detail modal view.
   - `MemoryExplorer`: Renders SQLite facts, observations, and security audit log table.

### Tier 2: Boundary & Corner Cases
Exercises defensive error handling and edge conditions:
1. **Empty Data Handling**: Empty transcripts directory, zero facts in `memory.db`, empty `audit.log`, zero benchmark runs in `eval.jsonl`.
2. **Missing & Invalid Parameters**: Out-of-bounds pagination (`limit=-1`, `offset=999999`), missing required search query params.
3. **Corrupt/Malformed Data**: Malformed JSON lines in `eval.jsonl`, non-existent or corrupted SQLite database file, unparseable audit lines.
4. **Zero & Extremes**: Zero token usage, 0ms latency, high latency (>60,000ms), 0% success rate, 100% failure rate.
5. **Invalid Filters**: Querying non-existent agent names or unsupported severity levels (`severity=INVALID`).

### Tier 3: Cross-Feature Interactions
Validates data consistency across modules:
1. **Aggregation vs Session History Consistency**:
   - Verifies `totalRuns` in `/api/metrics` matches the sum of persona runs in `/api/agents` and total count in `/api/sessions`.
2. **Audit Severity & Agent Status Correlation**:
   - High-severity security audit events correctly reflect in `/api/memory` and aggregate in agent audit indicators.
3. **Memory Query Filtering vs Agent Association**:
   - Querying facts filtered by persona returns persona-scoped memories without cross-contamination.

### Tier 4: Real-World Workload Scenarios
Simulates production-like multi-user and multi-persona operational patterns:
1. **Full Dashboard Boot & Hydration**:
   - Simulates parallel client fetches to `/api/agents`, `/api/metrics`, `/api/memory`, and `/api/sessions`, verifying zero race conditions or runtime crashes.
2. **Interactive Filtering & Search Workload**:
   - Simulates rapid search filtering on session transcripts combined with audit severity filter changes.
3. **Large Telemetry Ingestion Stress**:
   - Validates system performance when parsing datasets with hundreds of session logs, ensuring latency remains under threshold and responses complete without timeouts.

---

## 3. Test Runner & Execution Guide

```bash
# Run complete test suite (all tiers)
npm test

# Run tests in watch mode during development
npx vitest

# Run specific test file
npx vitest src/tests/api.test.ts
```

---

## 4. Test Integrity & Quality Standards

- **Opaque-Box Verification**: All assertions inspect external JSON payload contracts or rendered DOM nodes.
- **No Facade/Dummy Mocks**: Tests execute against real or properly structured mock fixtures conforming to `~/.sakthai/` schemas.
- **Zero Flakiness**: All async operations use deterministic promises and proper test setup/teardown.
