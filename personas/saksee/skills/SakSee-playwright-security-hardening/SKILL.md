---
name: SakSee-playwright-security-hardening
category: testing
description: "Centralize security and isolation test patterns for Playwright: CSP/cookies/cross-origin behavior and other browser-layer boundaries."
version: 1.0.0
---

# Playwright Security Hardening

Centralize security and isolation test patterns for Playwright: CSP/cookies/cross-origin behavior and other browser-layer boundaries.

## When to use

Use this skill when validating security-related browser behavior that cannot be exercised from backend unit tests alone.

## Steps

1. Test explicit boundary failures first: cookie domain/path/secure/SameSite leakage.
2. Validate CSP report-only vs enforced headers under realistic navigation.
3. Cross-origin checks: iframe permissions, message handlers, postMessage origin allowlist.
4. Authz: assert protected routes redirect or block without tokens, and forward tokens only to intended origins.

## Pitfalls

- extra HTTP headers or `host` overrides can hide CSP issues; do not normalize too aggressively.
- localStorage/sessionStorage assertions are stateful—clear in beforeEach.
