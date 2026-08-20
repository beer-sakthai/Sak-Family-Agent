---
name: SakKing-playwright-multi-context-orchestration
category: playwright-growth
description: Advanced Playwright skill for orchestrating multiple browser contexts
  within a single test. Use this when you need to verify cross-user interactions,
  multi-tenant isolation, real-time collaboration, or any scenario requiring two or
  more independent browser sessions in one deterministic flow.
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
    source: hermes:playwright-multi-context-orchestration
---

## Prerequisites

- Playwright installed (`npx playwright install chromium`)
- A running app reachable from localhost (or any host your browser can reach)
- Node.js >= 18

## Tool Calls (3+)

### 1) Spin up two isolated contexts with separate storage states

```ts
import { test } from '@playwright/test';

test('multi-user chat isolation', async ({ browser }) => {
  // Context A: Alice
  const alice = await browser.newContext({ storageState: 'state-alice.json' });
  const alicePage = await alice.newPage();
  await alicePage.goto('http://localhost:3000');

  // Context B: Bob (separate cookies / localStorage / sessionStorage)
  const bob = await browser.newContext({ storageState: 'state-bob.json' });
  const bobPage = await bob.newPage();
  await bobPage.goto('http://localhost:3000');
});
```

### 2) Exchange messages via the app and assert cross-context visibility

```ts
// Bob sends a message
await bobPage.fill('[data-testid=chat-input]', 'hello from Bob');
await bobPage.click('[data-testid=send-button]');

// Alice sees Bob's message (eventual consistency)
await alicePage.waitForSelector('[data-testid="message-Bob"]', { timeout: 5000 });
const text = await alicePage.textContent('[data-testid="message-Bob"]');
expect(text).toContain('hello from Bob');
```

### 3) Use `request` fixture for backend seeding before browser actions

```ts
// Use the test's request context to seed chat room via API
await test.info().annotations.push({ type: 'setup', description: 'seed room' });
const api = await test.info().project.request.newContext({ baseURL: 'http://localhost:3000' });
await api.post('/api/test/seed-room', { data: { roomId: 'room-42', users: ['alice', 'bob'] } });
```

### 4) Clean up contexts deterministically

```ts
await Promise.all([
  alicePage.screenshot({ path: 'alice.png', fullPage: true }),
  bobPage.screenshot({ path: 'bob.png', fullPage: true }),
]);
await Promise.all([alice.close(), bob.close()]);
```

## Advanced Variants

- **Same-page isolation**: use `browser.createBrowserContext()` to test third-party widgets without cookies leaking.
- **Live trace correlation**: `await context.tracing.start({ screenshots: true, snapshots: true })` per context; export combined trace (`playwright show-trace trace.zip`) and inspect interleaved events.
- **Network diffing**: expose `browser.newContext({ extraHTTPHeaders: { ... } })` to simulate tenant-specific headers and assert SSR/API behavior.

## Pitfalls

- Default `storageState` files are per-profile; don’t share one across contexts.
- `page.request()` shares cookies with its parent context (by design); use separate `api` contexts if you need a clean cookie jar.
- Tracing bundle size grows quickly with many contexts — limit to essential steps or trim with `--max-snapshots`.

## Verification

Run the bundled proof-of-concept file after creating it:

```bash
npx playwright test multi-context-demo.spec.ts --headed --workers=1
```

Expect two green tests:
1. `userA sees their own new message`
2. `userB sees userA's new message`
