---
name: sakthai-playwright-accessibility-testing
category: dogfood
description: Use Playwright’s built-in hooks for axe accessibility scanning, geolocation
  permissions, device emulation, responsive viewport checks, and permission gating
  to catch regressions early in headless browser flows.
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
    source: hermes:playwright-accessibility-testing
---

# Playwright Accessibility Testing for Browser Automation

## Problem

Automated QA often stops at visual/functional checks and misses common accessibility regressions, regional/locale-specific layout breaks, geolocation-dependent flows, and permission-gated features. This skill documents Playwright-specific accessibility, device emulation, and permission patterns not covered by the generic Playwright skills already shipped in the catalog.

## When to Use

- You want automated a11y checks as part of a cron/CI run
- A flow breaks only in certain locales, timezones, or device viewports
- You need to validate a permission-gated feature (geolocation, notifications, camera) without manual steps
- You want deterministic headless evidence for an accessibility issue to file or fix

## Core Capabilities

### 1. Axe Accessibility Scans

Playwright pairs naturally with `@axe-core/playwright`. Use AxeBuilder to surface missing labels, contrast failures, duplicate IDs, and ARIA issues.

- Scan the full page
- Constrain scans to a specific container
- Restrict to WCAG 2.1 A/AA rule tags

Use WCAG-tagged scans for compliance-style tickets; full scans for general QA sweeps.

### 2. Exclude and Analyze Specific Regions

When a page has known cosmetic regions or third-party widgets, narrow the scan with `.include()` and `.exclude()` to avoid noise and focus on app-owned DOM.

### 3. Geolocation and Device Emulation

Cron/CI runs need deterministic environment state. Playwright supports:

- Geolocation override with a fixed `latitude`/`longitude`/`accuracy`
- Device descriptors from the built-in registry for responsive/tablet/mobile behavior
- Viewport overrides for single-page responsiveness tests
- User agent and `isMobile` flags when you need explicit mobile behavior on desktop Chromium

### 4. Permissions and Offline State

Use `context.grantPermissions([...])` to pre-authorize features like geolocation, notifications, or camera so permission prompts don’t stall an automated flow.

Network conditions can also be hardened: offline mode, reduced data, throttling. These help verify degraded UX and fallback behavior in the same test flow.

### 5. CI-Friendly Reporting

Because Playwright’s accessibility snapshot is plain JSON, you can persist `violations` and `passes` to disk and diff across runs without opening a browser UI.

Keep files small by restricting tags and including only the relevant DOM subtree when possible.

## Workflow

1. Open a browser context with the desired device/locale/timezone/permissions.
2. Navigate to the target state and wait for the DOM region of interest.
3. Run an Axe scan.
4. Route violations into a structured artifact for review.
5. For follow-up, replay in `playwright test --debug=cli` or attach a trace snapshot.

## Anti-Patterns

- Don’t scan before the UI has reached the expected state—wait for the relevant locator.
- Don’t exclude large third-party containers if they touch app-owned accessibility properties.
- Don’t assume geolocation-dependent UI without also asserting fallback UI and permission-denied states.
- Don’t block all tracker domains before scanning if the app under test depends on a CDN-hosted font or widget.

## Verification

After applying these patterns:

1. Re-run the accessibility job and confirm violations JSON is written.
2. Confirm the scan passes when no known issues are injected.
3. Confirm the scan fails when a known a11y issue is intentionally introduced.
4. Confirm device/locale overrides affect the expected page behavior.
