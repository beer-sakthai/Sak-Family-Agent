---
name: playwright-html-reports
description: "Playwright HTML Test Reports: inspect test results via a filterable dashboard with browser, pass/fail/skip, and time-travel step inspection."
version: 1.0.0
author: SakSit
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [playwright, testing, reporting, html-reports]
---

# Playwright HTML Test Reports

## Concept
`npx playwright show-report` opens the HTML Reporter dashboard that aggregates test results after a run. It lets you filter by browser, status (passed, failed, skipped, flaky), and inspect errors, attachments, and step-level detail in one place.

## When to use
- After `npx playwright test` finishes; inspect failures or flaky tests without rerunning.
- When you need a shareable report for a PR or CI artifact.
- To drill from a failing test into DOM snapshots, network waterfalls, and console logs per step.

## How to run
```bash
# Run tests (creates/updates the report)
npx playwright test

# Open the report manually
npx playwright show-report
```

## Report features
- **Filterable dashboard**: browser, passed, failed, skipped, flaky.
- **Click a test** to see errors, attachments, and steps.
- **Auto-open** on failure only; use `show-report` for manual access.
- **Step inspection**: DOM snapshot before/after each action, network waterfall, console logs.

## Configuration
Enable explicitly in `playwright.config.ts`:
```ts
import { defineConfig } from '@playwright/test';
export default defineConfig({
  reporter: 'html',
});
```

## Pitfalls
- Report directory is `playwright-report/` (can be cleaned with `npx playwright clean-report`).
- Do not confuse with UI Mode (`--ui`); HTML reports are static snapshots from a run, while UI Mode is interactive.
- In CI, upload `playwright-report/` as an artifact so humans can inspect failures.

## Verification
Run a test with a known failure; confirm `npx playwright show-report` opens the dashboard and the failing test appears with expandable step details.
