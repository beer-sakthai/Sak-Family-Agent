---
name: SakKing-playwright-network-assertion
category: playwright-growth
description: Add deterministic network-level assertions to automation flows without
  relying solely on page content checks
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
    source: hermes:playwright-network-assertion
---

# Playwright Network Assertion

Use this skill when a test must verify network behavior rather than just UI state: API response status, payload shape, request headers, timings, and absence of unexpected endpoints.

## Purpose
Add deterministic network-level assertions to automation flows without relying solely on page content checks.

## Prerequisites
- `playwright` installed in the active environment.
- Node.js 18+ if running via `npx playwright test`; Python fallback can use `playwright.async_api`.
- Target endpoints reachable from test environment.

## Tool Calls
1. `playwright` route interception: `page.route('**/api/**', handler)` to inspect, mock, or assert requests.
2. `page.waitForResponse(urlOrPredicate)` to assert async responses with status/body/content-type.
3. `page.unroute(pattern, handler?)` to clean up listeners and avoid cross-test bleed.

Example pattern (Python):
```python
from playwright.async_api import Page, expect

async def assert_api_json(page: Page):
    response = await page.waitForResponse("**/api/endpoint")
    assert response.status == 200
    assert "application/json" in response.headers.get("content-type", "")
    body = await response.json()
    assert "id" in body
```

## Pitfalls
- Route matchers are order-sensitive; add broad routes before narrowing them.
- `waitForResponse` can time out if a later request also matches; prefer a predicate: `lambda r: r.url.endswith('/endpoint')`.
- Route handlers may swallow requests unless `fulfill()` or `continue_()` is returned; verify with explicit continuation when recording only.
- Network-parallel requests cannot be asserted with a single global wait if the page fires multiple matching responses; scope waits to a user action.

## Verification
Run a smoke test that asserts both success and failure cases:
1. Success:Navigate to a page, click to trigger an API call, assert `200` and expected JSON shape.
2. Failure:Trigger an error response, assert the response status is `>=400` and the page surfaces fallback UI.

After completion, clean up routes with `page.unroute(...)`.
