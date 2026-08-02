---
name: SakThai-playwright-security-header-validation
category: playwright-growth
description: Use Playwright to verify that a page sends the security response headers
  you require (CSP, X-Frame-Options, Permissions-Policy, HSTS, Referrer-Policy, X-Content-Type-Options,
  COOP/COEP). Capture headers, evaluate policies, and fail the run when a required
  header is missing or the policy is too permissive.
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
    source: hermes:playwright-security-header-validation
---

# Playwright Security Header Validation

## Purpose

Hardening web apps requires checking that browsers actually receive the
intended HTTP security headers. This skill provides a reusable, scriptable
approach to:

- enumerate response headers,
- assert required headers exist with acceptable direct values,
- evaluate JSON-structured headers like `Permissions-Policy` and `Content-Security-Policy`,
- fail fast with a minimal report (no UI dependencies).

Use it for:
- CI gates on security posture,
- regression checks when headers are deployed via CDN or reverse proxy,
- auditing staged apps before a rollout.

---

## Prerequisites

- `playwright` installed in the active Python environment
- Targets accept unauthenticated `GET /` and common asset routes
- Optional: `pydantic` installed for structured reports (suggested, not required)

Install check:

```bash
python - <<'PY'
try:
    import playwright
    print('playwright ok')
except Exception as e:
    raise SystemExit('playwright missing: %s' % e)
PY
```

---

## Core workflows (tool calls)

1. **Capture request/response headers across routes**
   - `context.on('response', lambda response: {response.url(): dict(response.headers)})`
   - Collect per-URL headers, dedupe, normalize `Set-Cookie` values.

2. **Assert required headers exist**
   - For each required header key, confirm presence in response headers for the route.
   - Validate value matches an allowlist or regex (e.g., `^strict-dynamic$|'self'`).

3. **Evaluate structured policies**
   - Parse semicolon-delimited header features:
     - `Permissions-Policy` -> `feature_name=allowed_origin` pairs
     - `Content-Security-Policy` -> directive-value pairs using AST-like splitting
   - Assert disallowed features/directives are absent (e.g., `unsafe-inline` in `script-src` unless explicitly allowed).

4. **Summarize and exit with status**
   - Print one line per route: `ROUTE STATUS (pass|fail): reason`
   - Exit with code 0 only when all checks on a required route subset pass.

---

## Minimal proof of concept

This proof-of-concept is local-only by default; replace the URL with a real host
in CI. It demonstrates the intended behavior without network crawl:

```bash
python - <<'PY'
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright().start() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        seen = {}
        page.on('response', lambda r: seen.setdefault(r.url(), dict(r.headers)))
        await page.goto('about:blank')
        headers = seen.get('about:blank', {})
        required = ['content-security-policy', 'x-frame-options', 'permissions-policy']
        missing = [h for h in required if h not in headers]
        if missing:
            print('fail: missing headers -> %s' % ', '.join(missing))
        else:
            print('pass: required headers present on about:blank')
        print('observed headers:', {k: headers.get(k) for k in required})
        await browser.close()

asyncio.run(main())
PY
```

Expected local outcome: fail with missing headers because `about:blank` sends none.
Swap to a real URL to gain a passing result on hardened deployments.

---

## Prerequisites

In addition to the Playwright runtime requirements:

- A target URL or route list to audit
- A policy file or inline allowlist for each header family
- Node/Python choice: this skill defaults to Python, but tests can be ported to TS

---

## Pitfalls

- Different routes can return different headers; audit routes individually.
- CDN/WAF may inject headers after origin reachability, causing false negatives.
- `Content-Security-Policy-Report-Only` is not enforcement; don’t count it as protection.
- Case-insensitivity: header keys should be normalized to lower-case before checking.
- `Permissions-Policy` uses boolean features and tokens; parsing mistakes falsely report pass.
- Timeouts vs. missing headers: distinguish TTO errors from header absence to avoid flaky CI.

---

## Verification step

Run locally and in CI:

```bash
python scripts/playwright_security_header_check.py --url https://app.example.com --headers-required csp,xframe,hsts,permissions
```

A non-zero exit code with a one-line reason string means a missing or weak header.
