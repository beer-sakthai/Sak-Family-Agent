---
name: SakSit-playwright-ui-mode
description: "Playwright UI Mode: interactive watch mode, live step view, and time-travel debugging for test authoring and failure investigation."
version: 1
author: SakSit
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [playwright, testing, debugging, ui-mode, watch-mode]
---

# Playwright UI Mode

## Concept
`npx playwright test --ui` launches an interactive web UI on `http://localhost:9223` that shows live test results, step-by-step execution, and time-travel debugging. It combines watch mode with visual test inspection — no need to switch between terminal output, trace viewer, and editor.

## When to use
- Writing new tests and wanting instant feedback on every change
- Debugging a flaky or failing test interactively instead of rerunning blind
- Inspecting DOM snapshots, network requests, and console output per step in one place
- Time-traveling forward/backward through actions to pinpoint exactly where state diverges

## How to run
```bash
# From your project root (requires playwright installed)
npx playwright test --ui

# With a filter or specific file
npx playwright test --ui tests/example.spec.ts
```

## What the UI gives you
- **Test list** with pass/fail/skip status, updating on file save
- **Step timeline** with click, type, navigate, assert actions
- **DOM snapshot** before and after each action
- **Network waterfall** with request/response bodies
- **Console logs** and page errors per step
- **Source preview** pointing to the exact line in the test file
- **Time travel**: scrub through steps to rewind and replay state

## Filtering & focus
- Click any test to see its steps.
- Use the filter bar to show only failed, skipped, or flaky tests.
- Click a step to freeze the page at that moment and inspect locators/network.

## Pitfalls
- UI Mode opens a browser window on port 9223; headless-only sandboxes (no display) cannot use it.
- Requires Playwright 1.33+.
- It is slower than plain CI runs — use it for authoring and debugging, not pipelines.
- Keep `--trace on` and UI Mode separate; UI Mode already embeds step-level snapshots.

## Verification
- Save a test file after adding a locator; confirm the UI reruns and shows the updated step.
- For a failing test, open the failing step in UI Mode and inspect the DOM snapshot to confirm the locator mismatch.
