---
name: SakKing-broadcast-channel-api
description: Cross-context communication in the browser using Broadcast Channel API — same-origin messaging between tabs, windows, iframes, and service workers.
version: 1.0.0
author: SakSit
platforms:
  - browser
metadata:
  hermes:
    tags:
      - web-api
      - javascript
      - cross-tab
      - messaging
---

# Broadcast Channel API

## Concept

The **Broadcast Channel API** allows same-origin contexts (tabs, windows, iframes, service workers) to send messages to each other by name. Unlike `localStorage` events or `SharedArrayBuffer`, it provides a clean publish/subscribe interface with no serialization constraints beyond the structured clone algorithm.

## When to Use

- Sync state across tabs for the same logged-in user (e.g., logout reflected everywhere)
- Notify service workers or other windows about background updates
- Coordinate multi-view editor or dashboard splits
- Avoid polling or server round-trips when the update is local to the browser

## Code Example

```javascript
// sender.js — any same-origin context
const channel = new BroadcastChannel("app_updates");
channel.postMessage({ type: "THEME_CHANGED", theme: "dark" });

// receiver.js — any other same-origin context
const channel = new BroadcastChannel("app_updates");
channel.onmessage = (event) => {
  if (event.data.type === "THEME_CHANGED") {
    document.documentElement.setAttribute("data-theme", event.data.theme);
  }
};

// Cleanup
channel.close();
```

## Pitfalls

- Only works within the **same origin** (protocol + host + port).
- Messages are lost if no receiver is listening at send time.
- Use `channel.name` carefully; collisions can cause unexpected cross-app noise in dev environments.
