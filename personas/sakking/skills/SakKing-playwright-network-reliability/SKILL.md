---
name: SakKing-playwright-network-reliability
category: dogfood
description: Use Playwright’s request interception, network idle, response timing,
  and selective mock/abort patterns to harden browser workflows against flaky third-party
  dependencies.
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
    source: hermes:playwright-network-reliability
---

# Playwright Network Reliability for Browser Automation

## Problem

Automated browser sessions often fail for reasons outside the app under test: analytics pixels, ad networks, CDN blobs, or A/B testing scripts stall `waitForLoadState`, trigger timeouts, or produce spurious console noise. This skill documents Playwright-specific network-reliability patterns that are not covered by generic browser automation guidance.

## When to Use

- A page intermittently times out while resources still load slowly
- Console is flooded with 404s/500s from non-essentials
- Tests must run deterministically without external dependencies
- You need to measure real app payload latency while ignoring trackers

## Core Capabilities

### 1. Route-Based Mocking and Blocking

Prefer `page.route()` over broad navigation waits. Blocking non-essential domains makes load-state predictions far more stable than guessing timeouts.

Good defaults to block in QA runs:
- `*.doubleclick.net`, `*.googletagmanager.com`, `*.google-analytics.com`
- `*.facebook.net`, `*.amazon-adsystem.com`, `*.hotjar.com`
- `*.segment.io`, `*.intercom.io`, `*.fullstory.com`

```python
await page.route("**/*", lambda route:
    route.abort()
    if any(pattern in route.request().url
           for pattern in BLOCKED_PATTERNS)
    else route.continue_()
)
```

If the target site breaks without some third-party domain, use granular `route.fulfill()` instead of blanket abort.

### 2. Work with Network Idle Correctly

`waitForLoadState("networkidle")` waits for ~500ms of quiet. On chatty pages this is unreliable. Use a time-bounded hybrid instead:

```python
try:
    await page.waitForLoadState("networkidle", timeout=5000)
except TimeoutError:
    pass  # proceed after timeout if core content is ready
```

Pair with DOM-ready signals from the app when available rather than relying solely on network silence.

### 3. Distinguish App vs Tracker Errors

Instrument requests so console analysis fields tracker noise separately from application failures.

```python
def classify(url):
    return "tracker" if any(p in url for p in BLOCKED_PATTERNS) else "app"

errors = []
page.on("console", lambda msg:
    errors.append({"source": classify(msg.location["url"]), "text": msg.text})
)
```

This classification is especially useful for the dogfood workflow: tracker errors can be de-prioritized or noted as noise rather than surfaced as candidate bugs.

### 4. Capture Response Timing Without Polluting Tests

Prefer `page.on("response")` over `page.reload()` timing loops. Record only application responses:

```python
timings = []
page.on("response", lambda res:
    timings.append({
        "url": res.url,
        "status": res.status,
        "time": res.request.timing.get("responseEnd", -1),
    })
    if "api.example.com" in res.url
)
```

After a single meaningful user action, read `timings` instead of waiting for full page idle. This avoids false positives from long-lived tracker keep-alives.

### 5. Selectively Mock Expensive or Rate-Limited APIs

Use `page.route("**/api/search", lambda route: route.fulfill(...))` to turn a flaky external API into a predictable fixture entirely inside Playwright. This is usually more robust than stubbing `fetch` in-page, because it removes network variability before it reaches the browser.

## Anti-Patterns

- Don’t replace all flakiness with `page.waitForTimeout()` — it masks real regressions.
- Don’t block fonts or critical CSS without testing readability/rendering first.
- Don’t treat `networkidle` as authoritative on SPAs that poll sockets.

## Verification

After applying these patterns:
1. Re-run the dogfood workflow phases
2. Confirm console has fewer tracker errors
3. Confirm page actions still reach expected application endpoints
4. If blocking broke functionality, convert the offending abort to a targeted `fulfill`
