---
name: SakKing-playwright-html-report
description: "Playwright HTML Test Report: auto-open behavior, manual viewing, and filtering workflow."
version: 1.0.0
author: SakSit · Master of Business
platforms: linux, darwin, win32
metadata:
  hermes.tags:
    - playwright
    - testing
    - reporting
    - debugging
---

# Playwright HTML Test Report

## Concept
After every test run, Playwright generates an HTML report dashboard. By default, it **auto-opens only when tests fail**. When all tests pass, you must open it manually.

## When to use
- Investigating test failures and step-by-step traces
- Reviewing passed/failed/skipped/flaky tests in one dashboard
- Sharing test results with team members
- Auditing test stability across browser runs

## Core commands

```bash
# Run tests (report generated automatically)
npx playwright test

# Open report manually (required when all tests pass)
npx playwright show-report
```

## Filtering
The report supports filtering by:
- Browser (chromium, firefox, webkit)
- Status: passed, failed, skipped, flaky
- Search by test name or error text

Click any test to inspect errors, attachments, and step details.

## Workflow tips
1. Use `--headed` during local development to watch tests run live.
2. Use `--project=chromium` to isolate execution and reduce report noise.
3. Combine with UI mode (`--ui`) for time-travel debugging, but remember `show-report` is for post-run review.

## Pitfall
Do not assume the report opens on success. Automate CI artifact upload if you want persistent reports for green builds.
