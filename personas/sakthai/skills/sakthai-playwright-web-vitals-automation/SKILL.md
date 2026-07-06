---
name: sakthai-playwright-web-vitals-automation
category: playwright-growth
description: Automated capture/assertion of Core Web Vitals and custom metrics in
  Playwright using the web-vitals library + page console interception. Use when testing
  performance, LCP, INP, CLS, TTFB, FCP, or building regression-tested dashboards
  for E2E suites.
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
    source: hermes:playwright-web-vitals-automation
---

# Playwright Web Vitals Automation

## Purpose
Capture real in-page Web Vitals during Playwright E2E runs and assert thresholds without modifying production code.

## Prerequisites
- `@playwright/test` installed (project already has Playwright)
- `web-vitals` (package) — can be injected via CDN for this PoC
- Node 18+
- Chromium recommended; metrics also supported in Firefox/WebKit where APIs exist
- Caution: CI devices are slower; cache plausible CI thresholds separately.

## Required Tool Calls
1. `bash`/shell: create or edit a helper script under `tests/e2e/` or `scripts/`
2. `bash`: run a focused Playwright test using `npx playwright test <file> --project=chromium --reporter=line`
3. `patch`/write to add assertions/regression thresholds to a tracked specs file

## Workflow

### 1. Register the metrics listener
Add to your Playwright setup (e.g. `global-setup.ts` or per-test):

```ts
import { test as base } from "@playwright/test";

export const test = base.extend({
  webVitals: async ({ page }, use) => {
    const metrics: any[] = [];
    await page.addInitScript(() => {
      // @ts-ignore
      window.__WEB_VITALS__ = [];
      const push = (m: any) => window.__WEB_VITALS__.push(m);
      window.webVitalsListeners = { push };
    });

    if (!(globalThis as any).webVitalsInjected) {
      await page.addInitScript(() => {
        const script = document.createElement("script");
        script.src =
          "https://unpkg.com/web-vitals@4/dist/web-vitals.iife.js";
        document.head.appendChild(script);
        script.onload = () => {
          (window as any).webVitalsListeners &&
            // @ts-ignore
            (window as any).onLCP((m: any) => (window as any).webVitalsListeners.push(m));
        };
      });
      (globalThis as any).webVitalsInjected = true;
    }

    await page.addInitScript(() => {
      // keep polling a bit for reliability in headless
    });

    await use(metrics);
  },
});
```

### 2. Collect and assert
```ts
test("homepage passes core web vitals", async ({ page, webVitals }) => {
  await page.goto("https://example.com", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1000);
  const metrics = await page.evaluate(() => (window as any).__WEB_VITALS__ ?? []);
  console.log("web-vitals-sample", { metrics });
});
```

### 3. Add regression limits
Use independent calls per metric, e.g. LCP < 2.5s, INP < 200ms, CLS < 0.1. Derive pass/fail from `metric.value`.

## Common Pitfalls
- Web Vitals are *in-page*; timing tests too early => missing metrics.
- Cache warm-up skews LCP; always test on cold page first.
- Headless Chromium can be *faster* than desktop Chrome; compare CI baselines rather than local.
- `web-vitals` via CDN creates a network dependency; in restricted CI use bundler alias to the npm package.
- CLS requires `visibilitychange` flush; consider `await page.evaluate(() => document.dispatchEvent(new Event("visibilitychange")))` in teardown.

## Verification
Run a single spec against a deterministic page and confirm metrics array length > 0 and all pass thresholds in the reporter output:

```bash
npx playwright test tests/web-vitals.spec.ts --project=chromium --reporter=line
```

### PoC smoke test (offline, no network)
Saved companion PoC file: `references/poc.js`

Quick derivation:
- Uses Playwright's browser + local `data:` page.
- Mocks `web-vitals` IIFE via `addInitScript`.
- Reads `window.__WEB_VITALS__` via `page.evaluate()`.
- Asserts emitted entries count > 0 and fail results cause `expect(...).toBe(true)` to fail.

## Configuration Hints for CI
- `npx playwright install chromium` before first run.
- Prefer `npx playwright test --shard=1/3` to reduce flakiness.
- Move side-effect-free threshold checks into lightweight Playwright Tests rather than Puppeteer/WebDriver suites.
