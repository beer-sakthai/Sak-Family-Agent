---
name: SakKing-playwright-auth-flow-state-testing
category: playwright-growth
description: 'Scripted auth workflow coverage: login, session reuse, logout, and redirect
  state transitions with Playwright.'
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
    source: hermes:playwright-auth-flow-state-testing
---

# Playwright Auth Flow State Testing

**Purpose:** validate authentication lifecycle flows with Playwright — login, authenticated action reuse, logout, and redirect/state transitions — to catch flaky auth regressions early.

**When to use:**
- CI checks for OAuth/session regressions.
- Local reproduction of auth edge cases.
- Cross-browser smoke of login/logout paths.

## Prerequisites
- Node.js 18+
- `playwright@^1.49` and `@playwright/test`
- A test target with deterministic auth endpoints (or a local mock server)

## Tool calls

1. **Install deps**
   - Command: `npm i -D @playwright/test @axe-core/playwright`
   -then: `npx playwright install chromium`

2. **Run focused spec**
   - Command: `npx playwright test tests/auth-flow.spec.ts --project=chromium --reporter=line`

3. **Open HTML report**
   - Command: `npx playwright show-report`

## PoC
- Starts a tiny static mock server and exercises 3 assertions:
  1. `/login` accepts a known credential and redirects to `/dashboard`
  2. after login, `/api/me` returns a 200 with an email payload
  3. `/logout` clears session storage and redirects to `/login?next=/dashboard`

Run with:
```bash
npx playwright test tests/auth-flow.spec.ts --project=chromium --reporter=json:playwright-auth-flow-report.json
```

## Pitfalls
- 2FA blocks headless flows — mock the 2FA gate or run a headful test only.
- Session cookies single-origin by default — use `storageState` to preserve state across tests.
- Redirect loops cause 30s timeouts — assert `page.url()` after each navigation step.

## Verification
- Exit code 0 from `npx playwright test ...`
- `playwright-auth-flow-report.json` contains `"passed": 3`
- No `page.url()` mismatch against expected redirect URLs.
