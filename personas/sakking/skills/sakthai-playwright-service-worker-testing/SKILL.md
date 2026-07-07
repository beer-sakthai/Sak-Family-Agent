---
name: sakthai-playwright-service-worker-testing
category: playwright-growth
description: 'Use when testing/verifying service worker behaviors with Playwright:
  route SW fetch/handle events, mock caches/offline, assert indexedDB writes, and
  enable reproducible SW-driven scenarios in E2E and CI.'
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - playwright
    - service-worker
    - pwa
    - offline
    - e2e
    - hermes
    - playwright-growth
    related_skills: []
    source: hermes:playwright-service-worker-testing
---

# Playwright Service Worker Testing

Purpose: provide a reusable recipe to start, stop, and patch service workers inside a Playwright test context so that offline/cache/background-sync behavior becomes deterministic.

## Prerequisites

- Node >= 18
- Playwright >= 1.44
- A page/ fixture that serves a script registering a SW at `/sw.js`.
- `--disable-web-security` is **NOT sufficient**; disable only when needed at your own risk.
- Permissions and storage quotas cleared between tests when isolation matters.

## Tool Call Guide

1. `page.route('**/sw.js', route => route.fulfill({ status: 200, body: SW_CODE }))` — inject a SW inline.
2. `page.evaluate(() => navigator.serviceWorker.register('/sw.js'))` — install it into the test page.
3. `page.route('**/data.json', async route => { if (offline) return route.abort(); route.fulfill(...); })` — simulate loss of connectivity for resource loads the SW caches.
4. `page.context().grantPermissions(['notifications'])` — let the SW show/hide notifications during background sync tests.
5. `page.evaluate(() => navigator.serviceWorker.controller.postMessage({ type: 'CLEAR_CACHE' }))` — reset SW state between tests without reload.

## Pitfalls

- Playwright’s browser contexts share the same disk cache across fixes; restart the context to fully clear SW state.
- Service worker scope binds to its url path — `/sw.js` only covers `/` by default; deep routes need per-test SW or `--service-worker=all`.
- `page.unroute(...)` does not equal SW `skipWaiting() + clients.claim()`; call both if updating SW mid-test.
- Headless Chromium with `--disable-gpu` still runs SW threads, but they can be slower — add `expect(...).toBeOK({ timeout: 120000 })`.
- DCH vs Xvfb: SW still works; use headless=new for best support.

## Verification

1. Run `npx playwright test tests/sw/poc.spec.ts`; expect tests passing: installs, clears cache, serves offline fallback, and asserts indexedDB key exists.
2. Confirm SW shows `activated` in devtools protocol: `page.evaluate(() => navigator.serviceWorker.ready)` returns truthy.
3. Inspect `playwright-report/trace.zip` for `serviceWorker` category entries to confirm events were captured.

## Minimal Proof-of-Concept

Run from the skill root after creating the following two files:

```
/sw-poc.spec.ts
/assets/sw-demo.html
/assets/sw.js
```

Then:

```bash
npx playwright test sw-poc.spec.ts --reporter=line
```

Expected representative output:

```
Running 3 tests using 1 worker
  ✓ installs service worker and activates [892ms]
  ✓ clears cache and writes indexedDB record [401ms]
  ✓ intercepts fetch while offline falls back to cached [1.1s]
  3 passed (2.4s)
```

Confirm the test produced a trace zip so behavior is debuggable post-run.
