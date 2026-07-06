---
name: sakthai-playwright-web-font-loading-validation
category: playwright-growth
description: Use Playwright to detect and gate on web font loading behavior - font-display
  strategies, @font-face ready events, FOUT/FOIT, and font-load timing regressions.
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
    source: hermes:playwright-web-font-loading-validation
---

# Playwright Web Font Loading Validation

Use when a page relies on custom web fonts and you need to verify that fonts load, render, or fail gracefully in an automated flow.

## Purpose
- Ensure `@font-face` rules are applied.
- Verify `document.fonts.ready` signals completion or failure.
- Detect FOIT (text invisible until loaded) or FOUT (fallback swap) regressions.
- Assert font-load timing budgets.

## Prerequisites
- Playwright installed (`npx playwright install chromium`).
- A local HTML fixture or route pointing to the page under test.
- `--disable-gpu` in CI optional for consistent rendering.

## Core tool calls
1. `page.goto("file:///tmp/webfont-poc.html")`
2. `page.waitForFunction(() => document.getElementById("out")?.textContent !== "starting")`
3. `page.$eval("#out", el => el.textContent)`
4. `page.screenshot({ path: "font-output.png" })` for FOIT/FOUT evidence.

## Pitfalls
- `@font-face` with `src: local(...)` may succeed immediately; use network emulation to avoid false pass.
- Headless Linux containers often lack the requested font; prefer loaded-state assertions over pixel diffs unless the font stack is pinned.
- `font-display: block` can delay text visibility; compare timing against a budget.

## Verification
Run:
```bash
npx playwright test <file> --browser=chromium --reporter=line
```
Expect the test to pass when the `#out` element reports `loaded <ms>ms`.
