---
name: sakthai-playwright-element-state-gating
category: playwright-growth
description: Robust Playwright interaction patterns that gate automated actions on
  validated element states to eliminate flaky tests before they happen.
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
    source: hermes:playwright-element-state-gating
---

# Playwright Element State Gating

Eliminate a huge class of flaky tests by never interacting with an element until its state is explicitly validated.

## Tool Calls Used

- `locator.isVisible()` / `locator.isEnabled()` / `locator.isHidden()`
- `locator.waitFor({ state: "visible" | "hidden" | "stable" | "attached" })`
- `expect(locator).toBeVisible()` / `toBeEnabled()` / `toBeHidden()`
- `locator.hover()` / `locator.focus()` / `locator.click()`
- `page.evaluate(() => ...)` to inspect DOM state out-of-band

## Prerequisites

- Node.js >= 18
- `@playwright/test >= 1.40`

## Usage Pattern

```ts
const submit = page.locator('#submit-btn');

// Gate click on stable, visible state
await submit.waitFor({ state: 'visible' });
await expect(submit).toBeEnabled();
await submit.click();
```

Advanced — wait for a full state transition:

```ts
const modal = page.locator('#confirmation-modal');

await modal.waitFor({ state: 'visible' });
await page.locator('#confirm').click();
await modal.waitFor({ state: 'hidden' });
// Regression: assert modal is actually detached, not just CSS-hidden
await expect(modal).toBeHidden(); // Playwright verifies display:none or detached DOM
```

Out-of-band sanity check when Playwright auto-wait is insufficient:

```ts
const isAttached = await page.evaluate((sel) => {
  return !!document.querySelector(sel);
}, '#dynamic-widget');
expect(isAttached).toBe(true);
await page.locator('#dynamic-widget button').click();
```

## Pitfalls

- **Chaining excess waits adds latency.** Group assertions when possible.
- **Hover menus race conditions:** gate the hover target, not the submenu, before continuing.
- **`toBeEnabled()` fails under overlays** — a screenspot/pointer-events overlay will block even if visually clear.
- **Network race ≠ stable DOM** — `networkidle` is not a proxy for element readiness.
- **State flapping:** if expect races through visible→hidden→visible, use `waitFor({ state: 'visible' })` first.

## Verification

Create `tests/element-state-gating.spec.ts` and run:

```bash
npx playwright test tests/element-state-gating.spec.ts --retries=10
```

Pass means the test stayed stable across aggressive retries.
