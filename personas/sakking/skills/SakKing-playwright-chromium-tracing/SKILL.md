---
name: SakKing-playwright-chromium-tracing
category: dogfood
description: Capture and export Playwright Chromium trace files (trace.zip) programmatically,
  then inspect them in Playwright Trace Viewer for debugging, audits, and deterministic
  replay of cron-driven browser sessions.
version: 1.0.0
platforms:
- linux
- macos
- windows
metadata:
  sakthai:
    tags:
    - hermes
    - dogfood
    related_skills: []
    source: hermes:playwright-chromium-tracing
---

# Playwright Chromium Tracing for Browser Automation

## Problem

Headless browser runs inside cron/CI lose all rich debugging context once the process exits. Playwright's built-in Chromium tracing (`trace.zip`) captures DOM snapshots, network, console, screenshots, and action history. This skill documents how to enable, collect, and replay those traces from automation scripts and how to hand them off for inspection.

## When to Use

- A cron-driven browser task fails intermittently
- You need to show stakeholders or GitHub issues the full sequence that led to a failure
- Debugging a flaky Dogfood/Playwright workflow
- Archiving evidence of browser actions for audit/compliance
- Replaying a browser session deterministically without rerunning live

## Core Capabilities

### 1. Start Tracing at Context Creation

Enable tracing once when creating the browser context. All pages opened from that context are recorded automatically.

```python
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            recordHar={...},
            recordVideo={...},
        )
        await context.tracing.start(screenshots=True, snapshots=True)
        page = await context.new_page()
        ...
        await context.tracing.stop(path="trace.zip")
        await browser.close()
```

### 2. Name Traces with Stable, Job-Aware Filenames

Use timestamps + job identifiers so cron outputs are sortable and traceable back to a specific run.

```python
import datetime
path = f"traces/{datetime.date.today().isoformat()}-job-123.zip"
await context.tracing.stop(path=path)
```

Store traces under a dedicated directory that does not get cleaned by unrelated log rotation.

### 3. Inspect Without Re-running

Launch the Trace Viewer against a saved trace for immediate inspection.

```bash
playwright show-trace traces/2026-06-16-job-123.zip
```

Tip: On headless CI hosts, forward the viewer via SSH tunneling or export selected screenshots instead.

### 4. Export Targeted Screenshots on Failure

When a step fails, take a screenshot and break into the trace dump — this keeps the trace small and focused on the failing sequence.

```python
try:
    await page.click("text=Submit", timeout=5000)
    await page.waitForLoadState("networkidle")
except Exception:
    await page.screenshot(path=f"artifacts/failure-{ts}.png")
    await context.tracing.stop(path=f"traces/failure-{ts}.zip")
    raise
```

### 5. Attach Traces to Issue Reports

Bundle `trace.zip` plus a short markdown summary to a GitHub issue or Dogfood report. The trace viewer is a standard Playwright artifact, so most reviewer workflows will open it directly.

## 6. Add Structured Context Metadata to Traces

Playwright traces benefit from human-readable chapters, not just raw actions. Use trace chunks/markers to annotate intent and timing.

```python
await context.tracing.start(screenshots=True, snapshots=True)
page = await context.new_page()
await page.goto("https://example.com/login")
with context.tracing.start_chunk(name="login", title="Login flow"):
    await page.fill("#user", "u"); await page.fill("#pass", "p")
    await page.click("button[type=submit]")
await context.tracing.stop(path="traces/2026-06-16-login.zip")
```

This produces grouped, searchable sections inside `playwright show-trace`.

## Complementing Skills
This skill focuses on collecting and replaying trace artifacts.
Pair it with `playwright-tracing-context-markers` for standardized trace chapter schemas, metadata injection, and labeled flow annotation.

## Environment-Safe Execution (WSL / unsupported-host fallbacks)
Some CI/bootstrap environments cannot launch Playwright browsers because the host is not listed in Playwright’s supported browser matrix, or the browser build is absent. In that case:
- Prefer an offline metadata-only proof of concept when validating trace helper logic.
- Do not treat `playwright install` as the only recovery path; check for manual browser channel workarounds only when the project explicitly supports them.
- When a real browser is required, gate the run behind an environment check and surface a clear `unsupported-host` exit rather than running and failing at `launch()`.
- Keep representation/trace schema work decoupled from live browser execution.

## Verification

1. Run the traced Playwright workflow and confirm `trace.zip` exists.
2. Open it with `playwright show-trace trace.zip` and confirm actions, network, and screenshots appear.
3. If using in cron, verify the trace path is outside cache directories.
4. If adding context markers, confirm chapter names/titles appear as grouped entries in Trace Viewer.

## Verification

1. Run the traced Playwright workflow and confirm `trace.zip` exists.
2. Open it with `playwright show-trace trace.zip` and confirm actions, network, and screenshots appear.
3. If using in cron, verify the trace path is outside cache directories.
