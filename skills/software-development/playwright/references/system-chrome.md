# System Chrome workaround for Playwright

Use on hosts where the bundled Chromium build is unsupported and Google Chrome is available by system channels.

## Exact workaround

```bash
npx playwright install chrome --with-deps
```

## Playwright config

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

## Notes

- On Ubuntu 26.04/WSL-like hosts, this avoids Playwright’s default Chromium path.
- Server-side GUI is not required for headless runs.
- Verify with `google-chrome --version`.
