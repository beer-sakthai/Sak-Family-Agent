---
name: chrome-devtools
description: "Chrome DevTools Protocol (CDP) with Playwright: network interception, tracing, performance profiling, browser introspection."
version: 1.0.0
author: SakSee
license: MIT
tags: [playwright, chrome-devtools, cdp, automation, debugging, performance, network]
---

# Chrome DevTools Protocol (CDP) via Playwright

## What it is
Chrome DevTools Protocol (CDP) is the wire protocol Chrome DevTools uses to
inspect, debug, and control Chromium. Playwright exposes it through
`CDPSession` so you can do advanced browser automation that the high-level
API doesn't cover directly.

## When to use it
- Advanced network interception / emulation beyond `page.route()`
- Performance tracing and timeline capture
- Browser console / log capture with source contexts
- Memory / heap snapshots and CPU profiling
- Connecting to an already-running Chrome instance
- Inspecting security headers / CSP at the protocol layer

## How to enable in Playwright
```js
const { chromium } = require('playwright');
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage();
const cdpSession = await page.context().newCDPSession(page);
```

## Common CDP operations

### Block / allow specific URLs
```js
await cdpSession.send('Network.enable');
await cdpSession.send('Network.setBlockedURLs', {
  urls: ['*.png', '*.jpg', '*.css']
});
```

### Capture performance trace
```js
await cdpSession.send('Tracing.start', {
  categories: ['devtools.timeline', 'loading']
});
// ... perform actions ...
const { stream } = await cdpSession.send('Tracing.end');
```

### Get browser console logs
```js
await cdpSession.send('Log.enable');
cdpSession.on('Log.entryAdded', (entry) => {
  console.log('Console:', entry.entry.text);
});
```

### Heap snapshot
```js
await cdpSession.send('HeapProfiler.enable');
const { profile } = await cdpSession.send('HeapProfiler.takeHeapSnapshot');
```

## Host-specific notes (this rig)
- This host uses **system Chrome** (`channel: 'chrome'`, not bundled Chromium)
- Headless is default; headed works when DISPLAY/WSLg is available
- CDP endpoint for an existing Chrome: `http://localhost:9222`

## Resources
- Playwright CDPSession API: https://playwright.dev/docs/api/class-cdpsession
- DevTools Protocol Viewer: https://chromedevtools.github.io/devtools-protocol/
