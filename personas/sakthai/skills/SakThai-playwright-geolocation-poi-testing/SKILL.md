---
name: SakThai-playwright-geolocation-poi-testing
category: playwright-growth
description: 'Automate browser location-based workflows with Playwright: set geolocation/POI
  coordinates, intercept location-based API responses, verify nearby results and region-dependent
  UI. Use for mapping, geofencing, delivery, travel, and distance-based logic.'
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
    source: hermes:playwright-geolocation-poi-testing
---

# Playwright Geolocation & POI Testing

## Purpose
Systematically test web apps that depend on device geolocation or points-of-interest by controlling browser coordinates, mocking geolocation/watchPosition, stubbing network POI responses, asserting distances/bounds, and resetting state. This skill covers local testing only — it avoids external services that require structured authentication.

## When to Load
- Checking map/closest-store results in a local preview build
- Verifying region-locked content or address autofill flows
- Validating distance/sort/delivery window logic
- Drift-testing geolocation permissions + watchPosition behavior

## Prerequisites
- Playwright installed locally or via `npx playwright`
- App exposing a page where location can be submitted or map rendered
- Console or network hooks available to inspect distance calculations

## Key Playwright Calls
1. `page.context().setGeolocation({ latitude, longitude, accuracy })`
2. `page.route('**/poi', handler => handler.fulfill({ json: mockPois }))`
3. `page.locator('[data-testid*=store], .store-name, [aria-label*=Store]')`
4. `page.evaluate(() => ({ lat: navigator.geolocation, perm: navigator.permissions }))`

## Invocation Pattern
```js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const dataPath = path.join(__dirname, 'playwright-geolocation-poi-testing', 'data', 'mock-pois.json');
const outDir = path.join(__dirname, 'playwright-geolocation-poi-testing', 'artifacts');
fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ geolocation: { latitude: 37.7749, longitude: -122.4194, accuracy: 20 } });
  const page = await context.newPage();

  await page.route('**/api/v1/pois**', async route => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 'p1', name: 'Embarcadero', lat: 37.7949, lng: -122.3994, distanceM: 1100 }]) });
  });

  await page.goto('file:///home/sakthai/.hermes/skills/playwright-growth/playwright-geolocation-poi-testing/assets/demo.html');
  await page.screenshot({ path: path.join(outDir, 'geo-poi.png'), fullPage: true });

  const nearby = page.locator('.nearby-store');
  const count = await nearby.count();
  console.log('nearby stores:', count);

  await browser.close();
})();
```

## Pitfalls
- Desktop Chromium in CI may not expose secure geolocation if the URL is http; use https or chrome-extra args `--use-fake-device-media-features`.
- Distances shown by the browser often use road-network routing, which differs from Haversine distance.
- Permissions API can lie about state; watchPosition errors never surface until a callback runs.
- `browser.newContext({ geolocation })` only grants permission once; reset each test.
- Mock responses should preserve the shape the Production code expects, or assertions will read stale fallback values.

## Verification Step
Run the bundled PoC fixture to confirm controls are available:
```bash
npx playwright test ~/.hermes/skills/playwright-growth/playwright-geolocation-poi-testing/tests/poc.spec.js --reporter=list --timeout=120000
```

All-in-one PoC assertion command:
```bash
npx playwright test ~/.hermes/skills/playwright-growth/playwright-geolocation-poi-testing/tests/poc.spec.js --reporter=list --timeout=120000
```

## Expected outcome
Locators resolve: `page.locator('[data-testid=lat], [data-testid=lng]')` returns non-empty text matching the mocked coordinates, and the canonical command above returns PASS.
