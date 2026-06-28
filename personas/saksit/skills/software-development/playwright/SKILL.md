---
name: playwright
description: "Playwright browser automation: installation, script execution, common pitfalls."
version: 1.0.0
author: SakThai
license: MIT
tags: [playwright, automation, testing, browser]
category: software-development
---

# Playwright Automation

## Overview
Guidelines for using Playwright via Node.js in the Hermes environment.

## Sandbox runtime — read first
Your shell runs in a **Modal sandbox** (`nikolaik/python-nodejs:python3.11-nodejs20`,
Node 20, **headless only — no display**). Two consequences:

- **No persistent workspace, no pre-existing project.** The container is
  ephemeral and separate from the host — do **not** hunt for a project dir like
  `/home/...`, `/home/pn`, or `/home/saas`; they don't exist here. To work on an
  existing repo, **`git clone` it into `/tmp` first**. To start fresh, create the
  project under `/tmp` (below). Browsers install to `/root/.cache/ms-playwright`
  and persist only within the session.
- Always launch `headless: true`.

## Installation (one-shot bootstrap, once per session)
```bash
cd /tmp && npm init -y >/dev/null 2>&1 && npm i playwright@1.61.0 >/dev/null 2>&1
npx -y playwright@1.61.0 install --with-deps chromium
```
`--with-deps` pulls the required system libraries (libnss3, libgbm1, …) — without
it Chromium fails with missing `.so` errors. Verified working in this sandbox.

## Scaffolding existing projects
Re-running `npm init playwright@latest` is safe — it **will not overwrite** existing tests or config files. Good for refreshing scaffolding without losing hand-written work.

## Running a script
1. Save your script to a file, e.g. `script.js`.
2. Execute it with:
   ```bash
   node script.js
   ```
   or, for Playwright test files, use:
   ```bash
   npx playwright test
   ```

## Hello-World Example
Create `hello.js`:
```js
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://example.com');
  console.log('Title:', await page.title());
  await browser.close();
})();
```
Run with `node hello.js` and you should see: `Title: Example Domain`

## Web-First Assertions
Playwright Test uses **web-first assertions** (e.g., `expect(page).toHaveTitle()`, `expect(locator).toBeVisible()`) that auto-wait for the condition to match before failing. Unlike bare `assert` or manual `setTimeout` checks, they retry for the full timeout and produce actionable failure messages with a trace of what was actually seen.

Example:
```ts
import { test, expect } from '@playwright/test';

test('web-first assertion', async ({ page }) => {
  await page.goto('https://example.com');
  await expect(page).toHaveTitle('Example Domain'); // auto-waits and retries
  await expect(page.locator('h1')).toBeVisible();
});
```

When to use: whenever asserting DOM state, URL, network responses, or accessibility tree conditions. Avoid `waitForTimeout` and custom sleep-based assertions.

## Tips
- Use `await page.screenshot({ path: 'screenshot.png' })` to capture visuals
- Parallel browsers: `await Promise.all([chromium.launch(), firefox.launch(), webkit.launch()])`
- For fast tests, headless is the default: `chromium.launch({ headless: true })`

## Pitfalls & Fixes
| Symptom | Cause | Fix |
|---------|-------|-----|
| `libnspr4.so` / `libnss3.so` missing | Missing system libs | `apt-get install -y libnspr4 libnss3` |
| Browser crashes on start | Missing graphics libs (libgbm1, libdrm2) | Install list in *Prerequisites* |
| Playwright binary not found | Browsers not downloaded | `npx playwright install --with-deps chromium` |
| Permission errors | Write perms in working dir | Work under `/tmp` |
| "Can't find project / no such dir" | Looking for a persistent workspace that doesn't exist in the sandbox | Create under `/tmp`, or `git clone` the repo first |
| Overwriting existing tests on re-init | Running `npm init playwright@latest` twice blindly | Safe to re-run; it skips existing files |