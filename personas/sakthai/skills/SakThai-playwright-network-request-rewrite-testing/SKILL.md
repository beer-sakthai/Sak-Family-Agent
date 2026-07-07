---
name: SakThai-playwright-network-request-rewrite-testing
category: playwright-growth
description: 'Plan and validate request rewrite/mocking pipelines in Playwright: assert
  that outgoing requests were rewritten as intended using request pattern, post-distribution
  body, or route interception. Good for backend-for-frontend rewrites, API migration
  smoke tests, and header injection validation.'
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
    source: hermes:playwright-network-request-rewrite-testing
---

# Playwright Network Request Rewrite Testing

## Purpose

Validate that client-side or middleware request rewrites actually occurred. This is not just asserting network calls happened — it proves each call reached the endpoint with the headers, query params, and body the migration targeted.

## Tool calls

Use at least 3 of these in each test suite:

1. `page.route('**/api/chat**', handler)` — intercept candidate URLs so you can assert rewrite eligibility before they leave the page.
2. `page.route('**/api/v1/**', async route => { ...; await route.fulfill({ status: 200, body: '...' }) })` — harden the pipeline so downstream tests never depend on a live backend.
3. `expect(request).toHaveURL(/\/api\/v2\//)` after clicking or submitting — assert the app emitted the new base path.
4. `request.allHeaders()['authorization']` or `.postDataJSON()` — prove rewrite preserved downstream contract requirements.
5. `page.unroute('**/api/**')` after assertions — keep the suite isolated so one rewrite style cannot leak across tests.

## Prerequisites

- playwright >= 1.49 installed and browsers downloaded (`playwright install chromium`).
- Node >= 18 or Python >= 3.11 with the matching Playwright binding.
- Network logging enabled in target app/API gateway if validating a real upstream.
- Know the "before" URL/payload and the "after" contract you want to prove.

## Common pitfalls

- Forgetting `await route.fulfill(...)` leaves requests hanging; tests appear to timeout with no network error.
- Route regex greed: `**/*` swallows everything else. Prefer explicit `**/api/v1/**` patterns.
- SPA routing may issue requests before test setup. Add routes before `page.goto(...)` or use a waitForRequest/watchdog combo.
- `route.continue_()` is not a complete rewrite — it passes the original headers/body through unless you modify them explicitly.
- Cloudflare/proxy health checks can look like rewrite failures if they land on a different host; whitelist them in assertions.

## Verification

Run this command to show the skill works end-to-end:

```bash
playwright test -g "network-rewrite"
```

Or run the standalone PoC in the companion `scripts/verify_rewrite.py` file:

```bash
python scripts/verify_rewrite.py
```

Expected: the script prints one `PASS` line for each rewrite assertion and exits with code 0. If assertions fail, the script prints `FAIL` with an explanation.
