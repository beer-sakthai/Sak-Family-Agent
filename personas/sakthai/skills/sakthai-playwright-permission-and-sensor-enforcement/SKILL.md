---
name: sakthai-playwright-permission-and-sensor-enforcement
category: playwright-growth
description: Enforce browser permission boundaries and sensor/device API availability
  during automated tests
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
    source: hermes:playwright-permission-and-sensor-enforcement
---

# Skill: Playwright Permission and Sensor Enforcement

## Purpose
Enforce browser permission boundaries and sensor/device API availability during automated tests. Use for security-sensitive flows, privacy screens, feature-flagged sensor features, and CI environments where hardware-backed APIs may be absent.

## Tool Calls
- `page.context.grantPermissions([...], {origin})`
- `page.context.clearPermissions()`
- `page.evaluate(() => window.PermissionStatus || navigator.permissions)`
- `page.context.newCDPSession(page)`

## Prerequisites
- Playwright 1.49+
- Node.js 18+ or Python 3.11+
- Optional: Chromium for CDP-backed inspection.

## Pitfalls
- Permissions are origin-scoped; consider exact scheme/host when granting.
- Sensors, SecureElement, and Touch can be absent in headless or containerized environments.
- iOS WebKit has different permission prompt behavior than Chromium/Firefox.
- Do not leave elevated permissions around between tests; always clear or scope per test.

## Verification
Run the included proof-of-concept and confirm:
- denied geolocation fails before grant
- grantPermissions allows the page to report `granted`
- clearPermissions restores `prompt`
