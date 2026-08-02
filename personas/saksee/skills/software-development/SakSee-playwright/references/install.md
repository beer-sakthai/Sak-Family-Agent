# Playwright install notes

Use this when environment-specific failures appear: Ubuntu 26.04, WSL, missing GNOME/desktop libs, system Chrome channel.

## Verified exact commands on restricted/GUI-less Linux
```bash
# Install package Google Chrome + Playwright Chrome channel
npx playwright install chrome --with-deps
```

- Requires internet + sudo-capable apt via `--with-deps` on Debian/Ubuntu.
- Confirmed working when default Chromium is unsupported on the host.
- Verifies install with:
  - `google-chrome --version`
  - `npx playwright --version`

## Recommended config snippet for system Chrome
```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  use: { ...devices['Desktop Chrome'] },
  projects: [
    {
      name: 'Google Chrome',
      use: { ...devices['Desktop Chrome'], channel: 'chrome', headless: true },
    },
  ],
});
```

## Delivery note
`npx playwright install chrome` can install `google-chrome-stable` even on headless hosts; no GUI session is required.
