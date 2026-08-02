---
name: SakThai-playwright-console-error-enrichment
category: playwright-growth
description: Enrich Playwright run errors and test failures with browser console messages,
  network failures, and runtime exceptions. Use when debugging flaky failures or hardening
  E2E suites.
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
    source: hermes:playwright-console-error-enrichment
---

# playwright-console-error-enrichment
## Purpose
Attach structured context (console logs, uncaught exceptions, and failed network requests) to Playwright test failures so debugging moves from "what broke" to "why it broke" without rerunning.

## Prerequisites
- Node.js >= 18
- `playwright` installed
- Tests running with `playwright/test`

## Tool calls (minimum pattern)
1. `page.on('console', ...)` — capture console messages during the test
2. `page.on('pageerror', ...)` — capture uncaught runtime exceptions
3. `page.on('requestfailed', ...)` — capture failed network requests
4. `test.info().annotations.push(...)` or `test.info().errors.push(...)` — attach enrichment to the test report

## Example usage
```ts
import { test, type Page } from '@playwright/test';

export default test.extend<{ withEnrichment: Page }>({
  withEnrichment: [async ({ page }, use) => {
    const consoleMessages: string[] = [];
    const pageErrors: unknown[] = [];
    const failedRequests: { url: string; failure?: string }[] = [];

    page.on('console', (msg) => {
      const type = msg.type();
      consoleMessages.push(`[${type}] ${msg.text()}`);
    });

    page.on('pageerror', (err) => pageErrors.push(err));

    page.on('requestfailed', (request) => {
      failedRequests.push({ url: request.url(), failure: request.failure()?.errorText });
    });

    await use(page);

    if (consoleMessages.length || pageErrors.length || failedRequests.length) {
      test.info().annotations.push({
        type: 'playwright-console-error-enrichment',
        console: consoleMessages,
        pageErrors,
        failedRequests,
      });
    }
  }, { auto: true }],
});

test('example', async ({ withEnrichment }) => {
  await withEnrichment.goto('https://example.com');
});
```

## Pitfalls
- Missing `auto: true` on the fixture means the annotation exists but never enriches the test.
- `request.failure()` may return `undefined`; always guard before `.errorText`.
- High-volume console spam can bloat JSON reports; filter by `type === 'error'` first if needed.

## Verification
Run a small test that intentionally logs to the console and unhandles-promise-rejects a request, then confirm the JSON report contains the enrichment annotation under `reports/*/attachments` or `results[].annotations`.
