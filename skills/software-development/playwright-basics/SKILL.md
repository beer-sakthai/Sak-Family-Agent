---
name: playwright-basics
description: "Basic guide to using Playwright in a Node.js environment within the Hermes agent setup. Includes installation, required OS libraries, a hello‑world script, and common pitfalls."
version: 1.0.0
author: SakSee
license: MIT
tags: [playwright, testing, automation, node]
---

# Playwright Basics

## Overview
Playwright is a Node.js library for browser automation. It can launch Chromium, Firefox, and WebKit in headless mode, navigate pages, and interact with elements.

## Prerequisites (Linux)
The browsers need a set of system libraries. On Debian‑based systems install them with:
```
apt-get install -y libnspr4 libnss3 libatk-bridge2.0-0 libatk1.0-0 libxshmfence1 libdrm2 libgbm1 libxss1 libxrender1
```
These packages were required for the Chrome headless shell.

## Installation
From a project directory:
```
npm init -y
npm i -D playwright
```
Playwright will automatically download Chromium, Firefox, and WebKit binaries.

## Hello‑World Example
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
Run with:
```
node hello.js
```
You should see `Title: Example Domain`.

## Host-Specific Requirement (Linux/WSL)
On this host, Playwright must use the **system Chrome binary**. Bundled Chromium is not supported on this build.
```js
const browser = await chromium.launch({
  headless: true,
  executablePath: '/opt/google/chrome/chrome'
});
```

## Common Pitfalls & Fixes
| Symptom | Cause | Fix |
|---------|-------|-----|
| `error while loading shared libraries: libnspr4.so` | Missing `libnspr4` | `apt-get install -y libnspr4` |
| `error while loading shared libraries: libnss3.so` | Missing `libnss3` | `apt-get install -y libnss3` |
| Browser crashes on start | Missing graphics libraries (e.g., `libgbm1`, `libdrm2`) | Install the list in *Prerequisites* |
| `BrowserType.launch: executable doesn't exist` | Playwright tried bundled Chromium on an unsupported build | Use `executablePath: '/opt/google/chrome/chrome'` |
| Python `ModuleNotFoundError: No module named 'playwright'` after `pip install` | System Python is externally managed (PEP 668) | Use a virtualenv instead of system Python |
| `EACCES` on packaged headless-shell binary | Sandbox/permission restriction on packaged runtime | Fall back to system Chrome |

## Verification
After installing the OS libs and Playwright, run the hello‑world script with the host-specific executable path. The console output should be:
```
Title: Example Domain
```
If you see that, the environment is ready for further Playwright tests.

## Usage Tips
- Use `await page.screenshot({ path: 'screenshot.png' })` to capture visuals.
- For fast tests, launch with `{ headless: true }` (default).
- Parallel browsers: `await Promise.all([chromium.launch(), firefox.launch(), webkit.launch()])`.

---

*This skill was created to capture the steps needed for Playwright usage within the Hermes agent environment.*