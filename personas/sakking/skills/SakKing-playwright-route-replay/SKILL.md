---
name: SakKing-playwright-route-replay
category: dogfood
description: Use Playwright route interception and HAR replay to run headless browser
  automations offline against recorded network responses, enabling deterministic replay,
  flaky-dependency isolation, and zero-network CI runs.
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
    source: hermes:playwright-route-replay
---

# Playwright Route Replay for Deterministic Browser Automation

## Problem

Cron-driven Playwright jobs depend on live network, third-party ads, auth redirects, and CDN timing drift. That makes runs non-deterministic, flaky, and hard to archive. `playwright-chromium-tracing` and `playwright-trace-har-bundle` capture evidence, but they still replay against live URLs. This skill adds the missing layer: **offline, deterministic, route-based replay** using HAR recordings and `page.route()` / `page.routeFromHAR()`.

## When to Use

- Re-run a captured browser flow without touching the live site
- Debug flaky flows that are stable in trace playback but fail on re-run
- CI jobs where external calls must be blocked or frozen in time
- Auditing/regression capture: freeze a known-good response snapshot and diff against it
- Offline demo/recording runs with no outbound internet

## Core Capabilities

### 1. Record a HAR Alongside Live Runs

Add HAR recording to any existing Hermes browser wrapper or cron Playwright task. Pick a path, filter to only the origins you care about, and capture full request/response bodies.

```python
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await context.route.from_har(
            "artifacts/flow.har",
            url="**/api/**",
            update=True,
            update_method="minimal",
        )
        await page.goto("https://example.com/login")
        # ... interact ...
        await browser.close()
```

Notes:
- `update=True` writes the HAR in-place; keep it read-only when replaying.
- `url` glob keeps the file small and avoid leaking unrelated traffic.
- In cron, normalize the path under a job-specific directory.

### 2. Replay Offline with `page.routeFromHAR`

After recording, disable network and replay locked to the saved responses.

```python
await context.route_from_har(
    "artifacts/flow.har",
    not_found="abort",   # fail closed on missing entries
    url="**",            # scope wide during replay
)
await page.set_offline(True)
await page.goto("https://example.com/login")
```

This gives you a fully deterministic run where any unexpected request errors out immediately.

### 3. Time-Travel Between Snapshots

Keep dated HARs alongside screenshots/traces. To test a specific captured day:

```python
selected = f"hars/{date_str}/flow.har"
await context.route_from_har(selected, not_found="abort")
```

Combine with `playwright-chromium-tracing` and `playwright-trace-har-bundle` for packet-level auditability.

### 4. Partial Mocking Mixed with Live Calls

Some flows cannot be fully frozen. Route the flaky origins and let the rest through.

```python
await context.route_from_har("artifacts/flaky.har", url="**/unstable/**")
# Non-matched requests still hit the network
```

## Anti-Patterns

- Don’t ship HARs with auth tokens, session cookies, or PII to shared storage; route replay can replay secrets verbatim.
- Don’t record one giant `networkidle` dump and replay forever; upstream changes silently break hidden assertions.
- Don’t leave `update=True` on in CI; you want replay-only behavior in scheduled jobs.

## Verification

1. Record HAR on a known flow and confirm it includes the key responses.
2. Replay with `set_offline(True)` and confirm the run completes without external requests.
3. Compare screenshots from recorded vs replayed runs to detect response drift.
4. If failing, run `playwright show-trace` + HAR diff to confirm whether behavior changed or responses expired.
