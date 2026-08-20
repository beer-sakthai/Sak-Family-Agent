---
name: SakKing-playwright-network-testing
category: testing
description: Centralize Playwright network and request-level assertions into one skill for reliable DOM and API behavior testing.
version: 1.0.0
---

# Playwright Network Testing

Centralize Playwright network and request-level assertions into one skill for reliable DOM and API behavior testing.

## When to use

Use this skill when a test needs to assert on HTTP traffic, route or redirect behavior, request payload/response integrity, or simulated network conditions.

## Steps

1. Confirm server health before asserting network behavior (avoid flaky `ERR_CONNECTION_REFUSED` runs).
2. Route the traffic you care about: `page.route`, `page.routeFromHAR`, or `page.unroute`.
3. Assert at the narrowest layer first:
   - URL + method + status.
   - Specific header values or response JSON shape.
   - Request body matches expected schema.
4. Rewrite or block only what you intend to test; restore original routes in `afterEach`.
5. Use dedicated network contexts (`page.context().newPage()`) when parallel requests need isolation.

## Pitfalls

- route regex overlaps can swallow requests unexpectedly.
- order matters: register routes before `page.goto`.
- avoid asserting exact timing-sensitive req counts unless the suite controls timing.
