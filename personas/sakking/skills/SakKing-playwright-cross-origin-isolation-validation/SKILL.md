---
name: SakKing-playwright-cross-origin-isolation-validation
category: playwright-growth
description: Use when verifying Cross-Origin Isolation (COOP/COEP) and SharedArrayBuffer
  capabilities with Playwright.
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - playwright
    - e2e
    - cross-origin-isolation
    - coop
    - coep
    - sharedarraybuffer
    - security
    - perf
    - workers
    - hermes
    - playwright-growth
    related_skills: []
    source: hermes:playwright-cross-origin-isolation-validation
---

# Playwright Cross-Origin Isolation Validation

Purpose: provide a reusable Playwright-driven workflow to verify that an application correctly publishes Cross-Origin-Opener-Policy, Cross-Origin-Embedder-Policy, and the resulting SharedArrayBuffer / cross-origin isolation state desired by high-performance web apps (WASM threads, high-resolution timers, performance.measureUserAgentCheck).

## When to use

- Validating deployment of COOP/COEP headers.
- Confirming that a route meant to be isolated actually reports `crossOriginIsolated: true`.
- Regression-testing header changes across environments.

## Prerequisites

- Node.js >= 18.
- Browser context launched with `--disable-dev-shm-usage` optional.
- Playwright test runner (`npx playwright test`).

## Tool calls / steps

1. **Inspect headers** via `page.request` or network events:

    ```python
    coop = response.headers.get('cross-origin-opener-policy')
    coep_require = response.headers.get('cross-origin-embedder-policy', '').lower()
    coep_value = response.headers.get('cross-origin-embedder-policy-report-only', '')
    ```

2. **Classify COOP**:

    - Accept: `same-origin` or `same-origin-allow-popups`.
    - Reject: `unsafe-none`, absent, or other values.

3. **Classify COEP**:

    - Require-corp pass: `cross-origin-embedder-policy` contains `require-corp`.
    - Report-only pass: acceptable only if no require-corp value is present AND reporting endpoint is configured.
    - Otherwise fail.

4. **Validate crossOriginIsolated capability** in-page:

    ```javascript
    const { crossOriginIsolated } = window;
    ```

    Must be `true` for pages that intend to use `SharedArrayBuffer`, `Atomics`, or `performance.measureUserAgentCheck`.

5. **Smoke-test SharedArrayBuffer creation** in the page:

    ```javascript
    const buffer = new SharedArrayBuffer(1024);
    const view = new Int32Array(buffer);
    view[0] = 42;
    ```

    If `crossOriginIsolated` is true and this throws, surface the error.

## Pitfalls

- `report-only` headers do NOT make `window.crossOriginIsolated === true`.
- COOP `same-origin-allow-popups` is accepted but weakens isolation; annotate findings.
- Remote page loading may be blocked by COEP; for pure header validation, use `page.route()` to fulfill with local JSON.
- Some reporters log warnings only; check actual header values, not just console output.

## Verification

1. Run the PoC script — PASS prints COOP/COEP state and `crossOriginIsolated:` boolean.
2. Fail cases: missing COOP, missing COEP require-corp, `SharedArrayBuffer` constructor not available without isolation.
3. Use `--browser=chromium` for SharedArrayBuffer checks; Firefox/Safari may report isolation differently.
