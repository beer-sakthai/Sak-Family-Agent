---
name: sakthai-playwright-perf-budget-validation
category: playwright-growth
description: Use when you want Playwright tests to fail if a page exceeds a performance
  budget for JavaScript execution time, DOMContentLoaded, or custom frontend timing
  metrics. Combines real browser measurement with budget gating and trace/meta extraction
  for CI and E2E.
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - hermes
    - playwright-growth
    related_skills: []
    source: hermes:playwright-perf-budget-validation
---

# Playwright Perf Budget Validation

## Purpose

Automate enforcement of numeric performance budgets in Playwright. The skill turns a test run into a pass/fail gate based on actual browser timings, not synthetic assumptions. It is designed for CI queues and E2E pipelines where a regression should fail the build immediately.

## What it covers

- Live timing capture: `performance.timing`, LCP, FID, CLS, TBT, JS heap.
- Per-metric budget definitions with operators (`<=`, `>=`, `between`).
- Warm vs cold measurement loops.
- Traceable evidence: append markdown with before/after metrics and Pass/Warn reference line.

## Prerequisites

- Node.js >= 18
- Playwright test runner installed
- Browser binaries installed: `npx playwright install chromium`

Recommended Playwright environment variables:
- `CI=true`
- `TZ=UTC`

No API keys required.

## Core tool calls

### 1) Measure real page budgets

```ts
import { test, expect } from '@playwright/test';

test('homepage JS execution budget', async ({ page }) => {
  await page.goto('https://example.test', { waitUntil: 'domcontentloaded' });
  const metrics = await page.evaluate(() => {
    const t = performance.timing;
    const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return {
      domContentLoaded: nav?.domContentLoadedEventEnd ?? t.domContentLoadedEventEnd,
      loadComplete: nav?.loadEventEnd ?? t.loadEventEnd,
      responseEnd: nav?.responseEnd,
      domInteractive: nav?.domInteractive,
      transferSize: nav?.transferSize,
      encodedBodySize: nav?.encodedBodySize,
      decodedBodySize: nav?.decodedBodySize,
      lcp: performance.getEntriesByName('largest-contentful-paint').at(-1)?.startTime ?? null,
      cls: performance.getEntriesByType('layout-shift').reduce((a, e: any) => a + (e.value ?? 0), 0),
      fid: performance.getEntriesByType('first-input').at(0)?.processingStart ?? null,
    };
  });

  const budgets: Record<string, { budgetMs: number }> = {
    domContentLoaded: { budgetMs: 1200 },
    loadComplete: { budgetMs: 2700 },
    lcp: { budgetMs: 2500 },
    cls: { budget: 0.1 },
  } as any;

  const failures: string[] = [];
  if (metrics.domContentLoaded > budgets.domContentLoaded.budgetMs) {
    failures.push(`domContentLoaded ${metrics.domContentLoaded}ms > ${budgets.domContentLoaded.budgetMs}ms`);
  }
  if (metrics.loadComplete > budgets.loadComplete.budgetMs) {
    failures.push(`loadComplete ${metrics.loadComplete}ms > ${budgets.loadComplete.budgetMs}ms`);
  }
  if (metrics.lcp != null && metrics.lcp > budgets.lcp.budgetMs) {
    failures.push(`lcp ${metrics.lcp}ms > ${budgets.lcp.budgetMs}ms`);
  }
  if (metrics.cls > (budgets.cls.budget as number)) {
    failures.push(`cls ${metrics.cls} > ${budgets.cls.budget}`);
  }

  expect(failures, `Budget exceeded: ${JSON.stringify(metrics)}`).toEqual([]);
});
```

### 2) Cool-down повторные замеры (warm run)

```ts
async function warmMeasure(url: string, runs = 3) {
  const results = [];
  for (let i = 0; i < runs; i++) {
    const m = await page.evaluate(() => { /* same shape */ });
    results.push(m);
  }
  return results;
}
```

### 3) Persist budget evidence as markdown

```ts
const reportPath = 'perf-budget-report.md';
const now = new Date().toISOString();
const report = `
## Perf Budget Report

- Timestamp: ${now}
- URL: ${url}

| metric | value | budget | status |
|--------|-------|--------|--------|

${failures.map(f => `| ${f} |`).join('\n') || '| ALL WITHIN BUDGET |'}
`;

await require('fs').promises.appendFile(reportPath, report);
```

## Pitfalls

- First-run timing can exceed warm runs due to service worker install or cache priming.
- LCP/CLS need user interaction or load-state delay; use `page.waitForLoadState('networkidle')` only cautiously.
- Chromium timing can differ from production Chrome; pin browser versions.
- If tests run under high CPU load, outlier latencies can trigger false budget failures — add a retry with discard of max outlier.

## Verification

1. Create a deliberately slow local HTML page measuring `setTimeout(..., 2200)` before `DOMContentLoaded`.
2. Run `npx playwright test` for this skill.
3. Assert that the test fails with the expected budget violation.
4. Reduce timeout to 900ms and rerun; expect pass.
5. Confirm `perf-budget-report.md` contains a Pass/Warn line for the final run.
