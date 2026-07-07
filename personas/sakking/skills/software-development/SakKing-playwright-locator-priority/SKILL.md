---
name: SakKing-playwright-locator-priority
description: "Playwright locator priority: use user-facing locators (role, label, text) instead of CSS/XPath to build resilient tests. Covers the built-in locator hierarchy, filtering, and selector composition."
version: 1
author: SakSit
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [playwright, testing, automation, locators, selectors]
---

# Playwright Locator Priority

## Concept
Playwright locators are the foundation of auto-waiting and retry-ability. The framework offers a built-in priority of locators; using the right one dramatically reduces flaky tests.

## Recommended Locator Priority (highest to lowest)
1. **`page.getByRole()`** — reflects how users and assistive tech perceive the page (button, heading, checkbox, etc.). Pair with `{ name: 'Exact Name' }` for precision.
2. **`page.getByLabel()`** — for form controls with associated `<label>` text.
3. **`page.getByPlaceholder()`** — for inputs that have placeholder text but no label.
4. **`page.getByText()`** — for static text content (non-interactive elements).
5. **`page.getByAltText()`** — for images with meaningful alt text.
6. **`page.getByTitle()`** — for elements with a title attribute.
7. **`page.getByTestId()`** — uses `data-testid` by default; the most resilient when UI text/roles change.
8. **`page.locator('css=...')` / `page.locator('xpath=...')`** — last resort. Tied to DOM structure and breaks easily on refactors.

## Code Example
```ts
import { test, expect } from '@playwright/test';

test('login flow with prioritized locators', async ({ page }) => {
  await page.goto('https://example.com/login');

  await page.getByLabel('User Name').fill('john');
  await page.getByLabel('Password').fill('secret');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByText('Welcome, John')).toBeVisible();
});
```

## Filtering & Composition
- **Filter by text:** `page.getByRole('listitem').filter({ hasText: 'Product 2' })`
- **Filter by descendant:** `page.getByRole('listitem').filter({ has: page.getByRole('button', { name: 'Add to cart' }) })`
- **Negate:** `filter({ hasNot: page.getByText('Out of stock') })`
- **Combine:** `page.getByRole('button').and(page.getByTitle('Subscribe'))`
- **Alternatives:** `page.getByRole('button', { name: 'New' }).or(dialog).first()`

## Shadow DOM
All locators pierce open shadow roots automatically. XPath does not. Closed shadow roots are unsupported.

## Strictness
Locators are strict: an action like `.click()` throws if multiple elements match. Explicitly use `.first()`, `.last()`, or `.nth(i)` only when necessary; prefer a tighter locator instead.

## When to use
- Authoring new tests from scratch
- Refactoring brittle tests that rely on CSS/XPath
- Deciding which locator strategy to generate in codegen output
- Reviewing PRs that replace role/text locators with CSS selectors

## Anti-patterns
- Long CSS chains (`#tsf > div:nth-child(2) > ...`) — breaks on markup changes.
- XPath expressions tied to layout.
- Using `.click()` on a locator that matches multiple elements instead of filtering first.
