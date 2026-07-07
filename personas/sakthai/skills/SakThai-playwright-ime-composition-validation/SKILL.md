---
name: SakThai-playwright-ime-composition-validation
category: playwright-growth
description: Validate CJK and complex-text input behaviors in web apps using Playwright
  by simulating IME composition events, detecting compositionend/blur race conditions,
  and ensuring composed text is submitted before input loss. Use when your app has
  East Asian or emoji input flows and you need automated regression coverage for composition-state
  handling.
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
    source: hermes:playwright-ime-composition-validation
---

# Playwright IME Composition Validation

## Purpose

International text entry workflows often break because apps fire blur/enter handlers
before the browser finishes IME composition. This skill lets you actively probe those
edge cases with Playwright: simulate compositionstart, compositionupdate,
compositionend, and assert that committed text is delivered to your input / contenteditable
before blur or form submission.

## Prerequisites

1. Playwright installed: `npm install @playwright/test`
2. Browsers downloaded: `npx playwright install chromium`
3. Node.js >=18 with npm

## Core Workflow

1. Route to your target page.
2. Focus an IME-capable input/contenteditable.
3. Use Playwright keyboard dispatch plus custom `page.evaluate` to fire composition events.
4. Assert committed text before blur and after blur/save.

## Tool Calls

- `page.goto(url)`
- `page.locator("selector").focus()`
- `page.keyboard.down(key)` / `page.keyboard.up(key)`
- `page.evaluate(fn)` to dispatch `CompositionEvent` and inspect `document.activeElement`
- `page.screenshot()` to capture failure artifacts without network dependency

## Minimal Proof of Concept (POC)

Write `tests/ime-composition.spec.ts`:

```ts
import { test, expect } from '@playwright/test';

test('composed Japanese text survives blur', async ({ page }) => {
  await page.setContent(
    `<input id="name" /><div id="out"></div><button id="save">Save</button>`
  );
  const input = page.locator('#name');
  const out = page.locator('#out');
  const save = page.locator('#save');

  await input.focus();
  await page.evaluate(() => {
    const el = document.getElementById('name') as HTMLInputElement;
    el.value = '';
    el.dispatchEvent(new CompositionEvent('compositionstart', { data: 'にほん' }));
    el.dispatchEvent(new CompositionEvent('compositionupdate', { data: 'にほん' }));
    el.value = '日本';
    el.dispatchEvent(new CompositionEvent('compositionend', { data: '日本' }));
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  });

  await expect(input).toHaveValue('日本');
  await save.click();
  await expect(out).toHaveText('saved:日本');
});
```

Run it offline against the inline HTML:

```bash
npx playwright test tests/ime-composition.spec.ts
```

## Common Pitfalls

- **Over-reliance on `type()`**: `page.keyboard.type()` may not faithfully emit
  `compositionstart/update/end`. Use `page.evaluate()` to inject events.
- **Blur races**: Some frameworks blur on mousedown. `blur()` on a composed input
  may yield empty `value`. Always assert input value before blurring.
- **contenteditable differences**: Use `document.execCommand('insertText')` inside
  `page.evaluate()` or set `innerText` after compositionend instead of setting `value`.
- **Permissive Shadow DOM**: If the input is in Shadow DOM, use locator's `evaluate`
  on the scoped root, not the document.
- **Emoji input on Windows**: Some tools expose grapheme clusters differently. Compare
  lengths after `Array.from(text).length`, not `text.length`.

## Verification / Done Criteria

A healthy run:

1. The input field reports committed text (`日本`) immediately after compositionend.
2. Clicking a save button preserves committed text and the recorded output matches.
3. In CI, the test passes without coordinators, accessibility-tree polling, or flaky waits.
4. A failing scenario (compositionend + immediate blur, no input commit) should show
   `value == ''`, confirming the test actually catches composition races.
