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

## Runtime: LOCAL on the host (this profile, since 2026-06-20)
This profile now uses `terminal.backend: local` — your shell runs **directly on
the host** (a WSL2 box with **WSLg**, `DISPLAY=:0`), not in the Modal sandbox.
That means:
- You can see the **host filesystem** directly — e.g. `~/tmp/pw-poc/`. No need to
  clone into `/tmp`; just `cd` to the real project path.
- **Real Google Chrome is installed** (`/usr/bin/google-chrome`) and you can run
  **headed** so the window shows up on the laptop:
  ```js
  const { chromium } = require('playwright');
  const browser = await chromium.launch({ channel: 'chrome', headless: false });
  ```
  Verified: a headed Chrome window opened on the host via Saksee. For
  unattended/CI runs, headless is still fine.
- Host Node is v24; host browsers cache is `~/.cache/ms-playwright`.

### Signed-in Chrome (persistent profile)
To act as a **logged-in** user (Google, etc.), do NOT use `launch()` — it starts
logged out every time. Use a **persistent profile** so cookies survive between
runs:
```js
const { chromium } = require('playwright');
const ctx = await chromium.launchPersistentContext('/home/sakthai/.pw-chrome-profile', {
  channel: 'chrome', headless: false, viewport: null,
  args: ['--disable-blink-features=AutomationControlled'],
  ignoreDefaultArgs: ['--enable-automation'],
});
const page = ctx.pages()[0] || await ctx.newPage();
// ... already signed in; do work ...
await ctx.close();
```
- The profile dir `/home/sakthai/.pw-chrome-profile` is signed in **once by the
  user** via `~/tmp/pw-poc/signin-chrome.js` (a visible window where they enter
  credentials by hand — never script-type passwords). After that, every run that
  points at the same dir is already logged in.
- Helper to reuse it: `node ~/tmp/pw-poc/open-signed-in.js [url]`.
- **Only one Chrome can hold the profile at a time** — don't run two scripts
  against it concurrently (profile lock). Close one before starting another.

The Modal-sandbox notes below apply only if this profile is switched back to
`backend: modal`.

## Sandbox runtime (only if backend: modal)
In the Modal sandbox (`nikolaik/python-nodejs:python3.11-nodejs20`, Node 20):
- **No display** — always launch `headless: true`.
- **Ephemeral container** — browsers install to `/root/.cache/ms-playwright` and
  persist within a session, but a fresh session needs the bootstrap again.
- **No persistent workspace, no pre-existing project.** Don't hunt for a project
  dir like `/home/...`, `/home/pn`, or `/home/saas` — they don't exist in the
  sandbox. To work on an existing repo, **`git clone` it into `/tmp` first**; to
  start fresh, create the project under `/tmp`.
- **One-shot bootstrap** (run once per session, before the first launch):
  ```bash
  cd /tmp && npm init -y >/dev/null 2>&1 && npm i playwright@1.61.0 >/dev/null 2>&1
  npx -y playwright@1.61.0 install --with-deps chromium
  ```
  `--with-deps` is required — without it Chromium fails with missing `.so` errors.
- **Alternate headless shell** — in some sandbox configurations the default Chromium binary is not loadable. Use the Playwright headless shell instead:
  ```bash
  python -m playwright install chromium-headless-shell
  ```
  The binary lands under `~/.cache/ms-playwright/chromium_headless_shell-<ver>/chrome-headless-shell-linux64`. If launch fails with `EACCES`, run `chmod +x` on that binary. Launch with:
  ```js
  browser = await chromium.launch({
    headless: true,
    executablePath: '/root/.cache/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-linux64'
  });
  ```

### Preferred default on this host

Use **Node 20** and the **npm-installed `playwright` package**. Playwright 1.60
(currently installed) is confirmed working here after the browser + system-lib
bootstrap completes. Even if a project `.venv` exists, use Node unless the
user explicitly wants Python.

## Prerequisites
- Node.js (npm) must be available (checked via `which npm`).

## Installation
```bash
npm install -D playwright
# After install, fetch browsers (use --with-deps in the sandbox)
npx playwright install --with-deps chromium
```

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

## Recommended config
Use TypeScript by default. The template `templates/playwright.config.ts` includes
HTML reporter, one project, and sensible retry/screenshot/video settings.
Create it with:
```bash
cp ~/.hermes/profiles/sakthai/skills/software-development/playwright/templates/playwright.config.ts ./playwright.config.ts
```

## Running tests
```bash
# Run suite with list + html reporters
npx playwright test --reporter=list,html
```
HTML report: `playwright-report/index.html`

## Test project structure
- `tests/*.spec.ts` — Playwright test files
- `playwright-report/` — HTML report directory
- `test-results/` — screenshots, videos, error context per failing test

## Python alternative (verified)
Playwright also works from Python in this sandbox. Use the async API:
```bash
python3 -m pip install playwright
playwright install --with-deps chromium
```
Reference snippet:
```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://example.com")
        print("Title:", await page.title())
        await browser.close()

asyncio.run(main())
```

## Profiles boundary
When scripts write a new skill, the runtime defaults to `cross_profile: false` for paths under `/home/sakthai/.hermes/`. For the cross-profile playwright-minute learner, set `cross_profile: true` explicitly.

## Pitfalls & Fixes
- **Connection refused** – do not run tests against a local server that is not already started.
  Pair the server with `beforeAll` and retry the server health check first, or start the app before the test run.
- **Playwright binary not found** – install it as shown above.
- **Browsers missing** – run `npx playwright install` after the npm install.
- **Permission errors** – ensure you have write permission in the working directory.
- **System Chrome on restricted hosts** – on hosts where Playwright’s default Chromium is unsupported, install Google Chrome and target it explicitly: `npx playwright install chrome --with-deps`, then set `channel: 'chrome'` in the project. Run in headless mode on GUI-less environments.

## Test recording baseline
Use the companion template `templates/demo.spec.ts` as a starting point for:
- title / text assertions
- API endpoint validation
- click + state-change assertions

## References
- `references/install.md` – detailed install commands and verification steps.
- `references/test-recording.md` – recorded test run notes, artifacts layout, and rerun checklist.
- `references/system-chrome.md` – notes on `npx playwright install chrome --with-deps` and `channel: 'chrome'` usage on hosts where default Chromium is unsupported.

