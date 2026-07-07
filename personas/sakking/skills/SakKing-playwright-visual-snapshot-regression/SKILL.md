---
name: SakKing-playwright-visual-snapshot-regression
category: playwright-growth
description: Catch visual regressions in web UIs with Playwright screenshot diffs.
  Use when you need pixel-level change detection for components, flows, or responsive
  breakpoints without a heavy visual-test framework.
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - playwright
    - visual-testing
    - regression
    - screenshots
    - diff
    - e2e
    - hermes
    - playwright-growth
    related_skills: []
    source: hermes:playwright-visual-snapshot-regression
---

# Playwright Visual Snapshot Regression

Capture baseline screenshots, compare new runs pixel-by-pixel, and
produce diff artifacts for review. Intended for fast iteration inside
CI or local dev loops.

## When to use

- A component or page just got a layout/CSS change and you want proof it
  is intentional.
- Changes span many breakpoints; manual review is too slow.
- You already use Playwright for E2E but need visual coverage outside
  Jest or Cypress-style stacks.

## Prerequisites

- Playwright installed and browsers downloaded.
- `npx playwright test --version` succeeds.
- Optional but recommended: `sharp` or `pixelmatch` available for
  threshold math; Playwright's built-in `expect(page).toHaveScreenshot()`
  is sufficient for simple cases.

## Tool calls (3+)

1. List configured projects/utilities and confirm Playwright install.

```bash
npx playwright --version
npx playwright install --help | head -n 40
```

2. Create a snapshot testing spec with baseline + diff output folders.

```bash
mkdir -p tests/visual/baseline tests/visual/diff
```

3. Run the snapshot suite and save results.

```bash
npx playwright test tests/visual/ \
  --output=playwright-report \
  --reporter=list,json
```

## Workflow

1. Pick pages or components that should stay visually stable.
2. Store the first clean run as the baseline in
   `tests/visual/baseline/<route>.png`.
3. On every future run, Playwright compares against baseline and writes
   diffs into `tests/visual/diff/`.
4. Review diffs manually or gate PRs with a maximum allowed
   pixel-change percentage.

## Pitfalls

- **Font antialiasing** differs across OS; lock CI base image or use
  `fontAntialiasing` overrides.
- **Animations/GIFs** cause flaky diffs: disable animations before
  screenshots. Example in tests:

```typescript
await page.addInitScript(() => {
  window.__PLAYWRIGHT_DISABLE_ANIMATIONS__ = true;
});
```

- **Responsive shifts** need explicit `viewport` per test; otherwise
  default sizes drift between executors.

## Verification

After running the suite, verify:

```bash
ls tests/visual/diff | wc -l
ls tests/visual/baseline | wc -l
```

Both counts should match. Inspect any nonzero diff images and decide
whether to update baseline or fix the UI.
