---
name: SakKing-playwright-webauthn-storage
category: dogfood
description: Use Playwright’s WebAuthn virtual authenticator, credentials API, and
  Web Storage APIs to automate passkey flows and read/write browser storage state
  without UI workarounds or hardware.
version: 1.0.0
platforms:
- linux
- macos
- windows
metadata:
  sakthai:
    tags:
    - hermes
    - dogfood
    related_skills: []
    source: hermes:playwright-webauthn-storage
---

# Playwright WebAuthn + Web Storage Automation

## Problem

Authentication flows increasingly rely on passkeys (WebAuthn) or Web Storage state, and generic browser automation has no clean way to provision these without hardware keys or brittle UI hacks. Playwright 1.61 added first-class `browserContext.credentials` plus `page.localStorage` / `page.sessionStorage`, turning formerly opaque platform APIs into scriptable primitives.

## When to Use

- Tests must register/authenticate with passkeys without security keys
- QA sessions need deterministic storage state across environments
- You need to inspect TLS/connection info for tenant isolation or compliance
- CI browsers previously failed at MFA/passkey prompts and now need a hardware-free path

## Core Capabilities

### 1. Provision a Virtual Authenticator (Passkeys)

Use `browserContext.credentials` to inject a credential and satisfy `navigator.credentials.create/get()` without a physical device:

```python
ctx = await browser.new_context()
await ctx.credentials.create('example.com', {
  'id': credential_id,
  'userHandle': user_handle,
  'privateKey': private_key,
  'publicKey': public_key,
})
await ctx.credentials.install()
```

Pair this with `playwright-session-persistence` so passkey-backed sessions are captured in storage state and survive cron/CI restarts.

### 2. Read/Write Browser Storage Programmatically

Use the new Web Storage API to inspect or seed state before assertions:

```python
await page.locator('#login').click()
token = await page.localStorage.getItem('token')
assert token is not None

items = await page.sessionStorage.items()
for k, v in items.items():
  print(k, v)
```

Seeding storage directly lets you bypass OAuth redirect loops for smoke tests while still exercising the UI.

### 3. Inspect Security Details of Responses

Use `apiResponse.securityDetails()` and `apiResponse.serverAddr()` to assert on TLS or backend routing:

```python
async def record_security(res):
  if '/api' in res.url:
    sd = res.securityDetails()
    print(res.url, sd.protocol(), sd.issuer(), sd.validFrom())

page.on('response', record_security)
```

Useful for compliance QA and for debugging multi-region routing without packet captures.

### 4. Combine With Session Probing

When a passkey or storage-seeded session might be stale, probe a known authenticated marker before heavy flows — same lightweight probe pattern as `playwright-session-persistence`, but checking storage values or auth-bound DOM markers.

## Anti-Patterns

- Don’t persist private keys in `storage.json`; treat them as separate secrets injected from env.
- Don’t use virtual authenticators for production auth — they’re for test/automation only.
- Don’t depend on `sessionStorage` across navigations from different origins; it’s origin-scoped.

## Verification

1. Run a passkey-dependent flow headless; confirm no hardware prompts and successful auth.
2. Inspect `localStorage` after seeding to confirm values persist across reloads.
3. Confirm `securityDetails()` shows expected TLS metadata for target hosts.
4. Save `storage.json` after auth and reload context; confirm session reuse without UI re-auth.
