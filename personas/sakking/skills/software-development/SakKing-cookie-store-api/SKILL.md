---
name: SakKing-cookie-store-api
description: Use the Cookie Store API for modern, async cookie access instead of document.cookie.
version: 1.0.0
author: saksit
platforms:
  - browser
metadata:
  hermes:
    tags:
      - web-api
      - cookies
      - async
      - frontend
---

# Cookie Store API

## Concept
The Cookie Store API (`cookieStore`) provides a clean, promise-based interface for reading and writing HTTP cookies. It replaces the clunky synchronous `document.cookie` string parsing with async methods that handle URL encoding, security attributes, and same-origin scoping automatically.

## When to use it
- Reading/writing cookies in modern browsers (Chrome 58+, Edge 58+, Opera 45+; not yet in Firefox/Safari)
- When you need async cookie access to avoid blocking the main thread
- When you want type-safe, chainable cookie operations
- Service workers (via `ServiceWorkerGlobalScope.cookieStore`) for background sync logic

Avoid in production if you need Firefox/Safari support; use with a feature-detect fallback.

## Code example
```javascript
// Write
await cookieStore.set({
  name: 'session_id',
  value: 'abc123',
  expires: Date.now() + 86400000,
  sameSite: 'strict',
  secure: true
});

// Read
const cookie = await cookieStore.get('session_id');
console.log(cookie.value);

// Delete
await cookieStore.delete('session_id');

// Feature detect
if ('cookieStore' in navigator) {
  // Supported
} else {
  // Fallback to document.cookie
}
```
