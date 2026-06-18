---
name: sakthai-playwright-iframe-consent-isolation-testing
category: playwright-growth
description: 'Validate third-party iframe consent overlays (Consent Management Platforms,
  GDPR/CCPA) AND first-party storage isolation across Playwright browser contexts.
  Use this when you need to prove: (1) CMP banners render and accept/reject actually
  set cookies, (2) cookies/storage are partition-boundary aware, and (3) cross-context
  state never leaks across test contexts.'
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
    source: hermes:playwright-iframe-consent-isolation-testing
---

# Playwright Iframe Consent & Isolation Testing

## Purpose
Many pages embed third-party iframes that render Consent Management Platforms (OneTrust, Cookiebot, Didomi, etc.). Confirming that:
- the consent overlay appears,
- Accept/Reject is wired to first-party storage,
- `localStorage`/`sessionStorage`/`IndexedDB` do not cross browser-context boundaries,

is required for compliance and behavioural-testing correctness. This skill covers both.

## Key Concepts
- **CMP iframe**: `<iframe>` carrying vendor JS for consent UI.
- **Consent API**: `__tcfapi`, `__cmp`, `_ccpa`, or vendor-specific globals.
- **Context isolation**: each Playwright `browser.newContext()` gets a fresh cookie jar + storage unless explicitly bridged via `userDataDir` or shared `cookie.json`.

## Prerequisites
- Playwright >= 1.45 (for `addInitScript`, route interception).
- Node 18+.
- Optional: `consent-string` npm package for parsing TCF strings.
- `DEBUG=pw:api` can help inspect target iframes.

## Tool Calls
### 1. Detect CMP API presence
```ts
page.evaluate(() => {
  const apis = ['__tcfapi', '__cmp', '_ccpa'];
  return apis.reduce((acc, api) => {
    acc[api] = typeof (globalThis as any)[api] === 'function';
    return acc;
  }, {} as Record<string, boolean>);
});
```
### 2. Assert CMP call via TCF "addEventListener"
```ts
await page.addInitScript(() => {
  (window as any).__tcfapi = (cmd: string, ver: number, cb: Function) => {
    (window as any).__tcfapiCalls = (window as any).__tcfapiCalls || [];
    (window as any).__tcfapiCalls.push({ cmd, ver, ts: Date.now() });
    cb('tcmp.stub', { tcString: 'mock-tc-string', listenerId: '1' });
  };
});
```

### 3. Check storage partitioning across contexts
```ts
const ctxA = await browser.newContext({ storageState: undefined });
const pageA = await ctxA.newPage();
await pageA.goto('about:blank');
await pageA.evaluate(() => localStorage.setItem('x', 'A'));

const ctxB = await browser.newContext({ storageState: undefined });
const pageB = await ctxB.newPage();
await pageB.goto('about:blank');
const leaked = await pageB.evaluate(() => localStorage.getItem('x'));
expect(leaked).toBeNull(); // critical: must not leak
```

### 4. Wire network to confirm CMP cookies
```ts
const cmpHit = page.waitForResponse(r => r.url().includes('consent') || r.url().includes('cmp'));
// ... trigger accept/reject ...
await Promise.all([
  page.locator('#accept-all').click(),
  cmpHit,
]);
const cookies = await page.context().cookies();
expect(cookies.some(c => c.name.includes('consent') || c.name.includes('cookie'))).toBeTruthy();
```

### 5. Block CMP network calls (negative test)
```ts
await page.route('**/*consent*', route => route.abort('failed'));
await page.goto('https://example.com');
// accept CMPs should remain unblocked, page still loads
```

## Pitfalls
- CMP iframes load lazily; wait for `networkidle` or a body containing the vendor name.
- Cross-origin iframes cannot be scripted via `page.locator('iframe >> text=Reject')` — use `page.frameLocator('iframe[name=""]')`.
- `storageState` serialises cookies but NOT IndexedDB; use `userDataDir` to persist it.
- Safari's ITP prunes third-party cookies aggressively; tests may need `--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure` only for sanity checks, never for compliance assertions.

## Verification Step
Run the bundled script in `scripts/verify_consent_isolation.sh` (requires Node and Playwright). It should print `PASS` for three checks: CMP stub fires, storage is isolated, and a cookie-like key is recorded on "accept".

This document was automatically generated as part of the playwright-growth loop. Do not edit manually; update the generator if behaviour changes.
