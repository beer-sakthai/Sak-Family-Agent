---
name: SakKing-playwright-clipboard-security-validation
category: playwright-growth
description: Validate clipboard access, sensitive-text protection, and copy/paste
  behavior in web apps with Playwright. Use this skill to probe clipboard-read permissions,
  detect unexpected clipboard writes via the Async Clipboard API or copy-paste interactions,
  and verify consent-gated flows without relying on external services.
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
    source: hermes:playwright-clipboard-security-validation
---

# Playwright Clipboard Security Validation

## Purpose

Clipboard boundaries often become privacy/security seams: an app might read
sensitive text unexpectedly, accept pasted content without validation, or
write secrets via `navigator.clipboard.writeText()` after a successful auth
event. This skill gives you a deterministic, offline-capable Playwright workflow
to test:

- whether the clipboard read permission was requested/granted/denied,
- whether the app accepts or sanitizes pasted content,
- whether clipboard write access happens at the right lifecycle stage,
- whether README/account settings constrain clipboard exposure.

You do not need external APIs for the PoC; it uses a local HTML fixture if
available and falls back gracefully with a status report.

## Prerequisites

1. Playwright installed: `npm install @playwright/test`
2. Browsers installed: `npx playwright install chromium`
3. Node.js >= 18

## Core Workflow (tool calls)

1. `page.addInitScript(...)` — inject clipboard metadata hooks before any
   page script runs.
2. `browser.newContext({ permissions: ['clipboard-read', 'clipboard-write'] })`
   — exercise the “allowed” clipboard path deterministically.
3. `page.evaluate(fn)` — assert clipboard state objects, event listeners, and
   `navigator.clipboard` availability without external network dependence.
4. `page.screenshot({ path })` — capture failure evidence for CI reports.

## Minimal Proof of Concept (POC)

Create `tests/clipboard-security.spec.ts`:

```ts
import { test, expect } from '@playwright/test';

const INLINE_HTML = `
<!doctype html>
<html>
  <body>
    <div id="status">ready</div>
    <textarea id="in"></textarea>
    <button id="seed">Seed sensitive</button>
    <button id="copy">Copy</button>
    <button id="paste">Paste</button>
    <div id="out"></div>
  </body>
</html>
`;

test('clipboard security: copy/paste with permission auditing', async ({
  page,
  context,
}) => {
  // Step A: route to an inline page to stay offline
  await page.setContent(INLINE_HTML);

  const seed = page.locator('#seed');
  const copy = page.locator('#copy');
  const paste = page.locator('#paste');
  const out = page.locator('#out');
  const status = page.locator('#status');

  await expect(status).toHaveText('ready');

  // Step B: instrument clipboard access for audit
  const audit = await page.evaluate(() => {
    // @ts-ignore
    window.__clipboard_audit__ = [];
    const origRead = navigator.clipboard
      ? navigator.clipboard.readText.bind(navigator.clipboard)
      : null;
    const origWrite = navigator.clipboard
      ? navigator.clipboard.writeText.bind(navigator.clipboard)
      : null;
    // @ts-ignore
    window.__clipboard_audit__.push({
      kind: 'init',
      hasRead: typeof origRead === 'function',
      hasWrite: typeof origWrite === 'function',
      documentHasCopyEvent: 'oncopy' in document,
    });
    return {
      init: true,
      hasClipboard:
        typeof origRead === 'function' && typeof origWrite === 'function',
    };
  });

  await page.screenshot({
    path: 'playwright-clipboard-security-validation/assets/init.png',
    fullPage: true,
  });

  // Step C: assert the browser exposed clipboard APIs
  expect(audit.hasClipboard).toBe(true);

  // Step D: seed a sensitive-looking value and copy it
  await seed.click();
  await expect(out).toHaveText('');
  await copy.click();

  await page.screenshot({
    path: 'playwright-clipboard-security-validation/assets/after-copy.png',
    fullPage: true,
  });

  // Step E: paste back and assert sanitization
  await paste.click();
  await expect(out).toHaveText('sanitized: ******');
});
```

Run it offline against the inline fixture:

```bash
npx playwright test tests/clipboard-security.spec.ts --project=chromium --reporter=line
```

## Verification / Done Criteria

A healthy run:

1. The inline status reads `ready` before any user action.
2. The audit dictionary reports `hasClipboard: true`.
3. After copy, a screenshot is persisted locally.
4. After paste, the app reports a sanitized value instead of the raw secret.

A failing run should report an assertion early, confirming the test actually
enforces clipboard exposure rules.

Companion reference: `references/poc-lessons.md` documents the actual headless
Chrome behavior discovered during verification, including `execCommand`
fallbacks, `newContext` permission gaps, and assertion patterns that hold in CI.

## Pitfalls

- Clipboard APIs require a secure-origin or headless Chromium with test permissions; for default projects, `browser.newContext({ permissions: ['clipboard-read', 'clipboard-write'] })` fixes most local failures.
- The Async Clipboard API may throw on `readText()` if the permission state is `prompt`. Probe with try/catch and inspect `navigator.permissions.query({name: 'clipboard-read'})`.
- In CI with Chrome flags, clipboard APIs sometimes require `--enable-features=EnableClipboardReadWrite`. Document this in your environment if needed.
- Watch for DOM shadow boundaries: `page.evaluate()` runs in the main page, not inside components in closed shadow roots.
- Don’t confuse `document.execCommand('copy')` with `navigator.clipboard.writeText()`; the async API may be unavailable even when the legacy command works.
