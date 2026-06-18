---
name: sakthai-playwright-load-injection-and-sla-validation
category: playwright-growth
description: Automate synthetic load testing and SLA validation in CI or cron workflows
  by using Playwright to drive many parallel browser workers, collect timing telemetry,
  and assert hard latency/error-rate thr…
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
    source: hermes:playwright-load-injection-and-sla-validation
---

# Playwright Load Injection and SLA Validation

## Purpose
Automate synthetic load testing and SLA validation in CI or cron workflows by using Playwright to drive many parallel browser workers, collect timing telemetry, and assert hard latency/error-rate thresholds.

## Prerequisites
- Playwright installed with browser binaries.
- Python 3.11+ (or Node if porting TS).
- A target URL that returns deterministic JSON or has stable selectors.
- Optional: `pytest` and `pytest-xdist` for parallel test shards.

## Tool Calls to Use
1. `terminal("playwright install chromium")` — ensure browser binary is available.
2. `terminal("python3 poc_load.py --url https://example.com --workers 5 --sla 2000ms")` — run the PoC load script.
3. `terminal("python3 - <<'PY' ...")` — run inline aggregation script over a generated JSON report.

## Steps
1. Define an SLA contract (p95 latency, max error ratio, min throughput).
2. Spawn N Playwright workers, each looping a critical user journey for T seconds.
3. Record per-iteration timestamps and outcomes to JSON lines.
4. Post-process JSONL into percentiles and error counts.
5. Exit 1 and write a clear diff if SLA is breached.

## Pitfalls
- CI machines may throttle CPU; run with smaller worker counts.
- Network jitter can spike tail latency; prefer p95 over max.
- Avoid repeat-login hotspots; cache auth tokens when possible.
- Playwright tracing or video multiplies disk I/O; keep screenshots only on failure.

## Verification Step
Run: `python3 poc_load.py --url https://example.com --workers 2 --sla 5000ms`
Expected: green summary with `status=passed` and numeric p95 under SLA.
