---
name: SakSit-view-transition-api
description: "Use the native View Transition API for smooth SPAs and element-scoped DOM state animations without framework-specific setup."
version: 1.0.0
author: SakSit
license: MIT
tags:
  - view-transition
  - SPA
  - animation
  - dom
  - web-api
category: software-development
metadata:
  hermes:
    tags:
      - frontend
      - browser-api
      - css
---

# View Transition API

## Trigger
Use when you need smooth animated transitions between DOM states in a single-page app (SPA) or for an element-level view change, and you want a framework-agnostic, browser-native solution.

## Core concept
`document.startViewTransition(updateCallback)` (or `element.startViewTransition()`) lets the browser capture the old UI state, run your DOM update, then animate between the two states.

## Lifecycle promises
- **updateCallbackDone** – resolves when your DOM update finishes.
- **ready** – resolves when the old/new snapshots are captured and the transition is about to start.
- **finished** – resolves when animations end. Call `transition.waitUntil(promise)` to extend duration.

## CSS pseudo-element tree
```css
::view-transition
::view-transition-group(root)
::view-transition-image-pair(root)
::view-transition-old(root)
::view-transition-new(root)
```
Target `::view-transition-old()` and `::view-transition-new()` to customize outbound/inbound animations. Assign distinct `view-transition-name` values to animate specific elements independently.

## Minimal SPA example
```js
function updateView(newHtml) {
  if (!document.startViewTransition) {
    document.getElementById('app').innerHTML = newHtml;
    return;
  }

  document.startViewTransition(() => {
    document.getElementById('app').innerHTML = newHtml;
  });
}
```
Default behavior is a fade (opacity 1→0 for old, 0→1 for new).

## Element-scoped transitions
```js
container.startViewTransition(() => {
  container.innerHTML = newContent;
});
```
Only descendants of `container` participate; rest of the page is unaffected.

## Gotchas
- Skipped entirely if `document.visibilityState === 'hidden'` during the call.
- Old snapshot is static (non-interactive); new snapshot is interactive.
- Cross-document (MPA) transitions require same-origin nav and `@view-transition { navigation: auto; }`.
