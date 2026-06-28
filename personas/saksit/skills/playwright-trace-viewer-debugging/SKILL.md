---
name: playwright-trace-viewer-debugging
description: Use Playwright Trace Viewer to debug failing tests by recording traces and replaying them in the Playwright Trace Viewer UI.
version: 1
author: SakSit
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [playwright, testing, debugging, trace-viewer]
---

# Playwright Trace Viewer for Failing Test Debugging

## Concept
Playwright Trace Viewer is a GUI tool that replays recorded test traces with full DOM snapshots, network activity, console logs, and source code at each step. When a CI test fails and you cannot reproduce locally, the trace gives you a time-travel view of what actually happened.

## When to use it
- A test fails only in CI / headless / a specific browser
- You have a flaky test where the failure is hard to reproduce interactively
- You need to inspect DOM state, network requests, and console at the exact moment of failure
- Postmortem on a regression to compare two traces

## How to record a trace
1. Run with trace enabled:
   ```bash
   npx playwright test --trace on
   # or specifically for one test:
   npx playwright test --trace on tests/checkout.spec.ts
   ```
   Modes: `'off'`, `'on'` (always), `'retain-on-failure'` (only keep on failure — best for CI), `'on-first-retry'`.

2. Traces are written to `test-results/<test-name>/trace.zip`.

## How to view
```bash
# Local — opens browser GUI against the trace
npx playwright show-trace test-results/<test-name>/trace.zip

# Or via the Playwright CLI online viewer
npx playwright show-trace --port 8080
```

## Programmatic tracing (no test runner)
```js
const { chromium } = require('playwright');
const browser = await chromium.launch();
const context = await browser.newContext();
// Start tracing before navigation
await context.tracing.start({ screenshots: true, snapshots: true });
const page = await context.newPage();
await page.goto('https://example.com');
// Stop and save
await context.tracing.stop({ path: 'trace.zip' });
await browser.close();
```

## What the viewer shows
- Action timeline (click, type, navigate)
- DOM snapshot **before and after** every action
- Network waterfall with request/response bodies
- Console output and page errors
- Source of the test file at each step
- Screenshots at each action

## Pitfalls
- Trace files contain sensitive data (DOM, network responses, screenshots). Don't upload them to public artifact stores without scrubbing.
- `--trace on` slows tests ~2–3x. Use `retain-on-failure` in CI to limit overhead.
- Try-locator and strict mode violations appear in the trace — use them to diagnose the actual cause instead of guessing.

## Verification
- After fixing a test, re-run with `--trace on` to confirm the failure no longer reproduces.
- Compare two traces (before/after fix) in the viewer to confirm the behavior change.
