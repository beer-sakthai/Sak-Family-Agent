---
name: sakthai-playwright-visual-viewport-testing
category: playwright-growth
description: Validates and correlates physical, layout, and visual viewport metrics
  in real mobile/desktop contexts.
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
    source: hermes:playwright-visual-viewport-testing
---

# Playwright Visual Viewport Testing

## Purpose
Detect layout shifts, keyboard overlays, orientation changes, and on-screen address bar behavior that the Layout Viewport hides. Use this skill whenever your app targets mobile browsers, PWA installability, or in-app browsers.

## Prerequisites
- `playwright` installed in the active Python env (or use `npx playwright`).
- `chromium` browser downloaded (`playwright install chromium`).

## Tool Calls
1. `page.evaluate("() => ({width: window.visualViewport.width, height: window.visualViewport.height, scale: window.visualViewport.scale, offsetTop: window.visualViewport.offsetTop, offsetLeft: window.visualViewport.offsetLeft})")`
2. `page.setViewportSize({width, height})` followed by `page.waitForTimeout(100)` then re-evaluate visual viewport to correlate layout vs visual change.
3. `page.addInitScript("() => { window.__vvLog = []; const vv = window.visualViewport; vv.addEventListener('resize', () => window.__vvLog.push({type:'resize',w:vv.width,h:vv.height,scale:vv.scale,t:Date.now()})); }")` then perform interactions and collect `__vvLog`.

## Workflow
1. Start with a known `page.setViewportSize`.
2. Record both `layoutViewport` (innerWidth/innerHeight) and `visualViewport` sizes.
3. Trigger interaction that can bring up keyboard or collapse toolbar.
4. Assert the visual viewport delta matches the expected shift budget.

## Example
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    page = p.chromium.launch(headless=True).new_page(viewport={"width":390,"height":844})
    before = page.evaluate("""() => { const vv = window.visualViewport; return vv ? {w:vv.width,h:vv.height,s:vv.scale,t:vv.offsetTop,l:vv.offsetLeft} : 'missing'; }""")
    page.set_content("<input id=t autofocus>")
    page.focus("#t")
    page.wait_for_timeout(150)
    after = page.evaluate("""() => { const vv = window.visualViewport; return vv ? {w:vv.width,h:vv.height,s:vv.scale,t:vv.offsetTop,l:vv.offsetLeft} : 'missing'; }""")
    print({"before": before, "after": after})
```

## Support files
- `references/poc-lessons.md` — concrete headless-Chromium PoC findings and the evaluate-polling pattern that worked.

## Verification
The script prints a dict with non-null visual viewport metrics. In headless Chromium the OSK doesn’t appear, but the API still returns live values; verify `w` and `h` are numbers.

## Pitfalls
- Headless mode does not trigger OSK or toolbar collapse, but `window.visualViewport` **does** exist and returns live values. Don’t rely on event listeners firing headless — poll via `evaluate` at the moment you care about. See `references/poc-lessons.md`.
- `window.visualViewport` can be `undefined` in old WebKit; guard with `if (window.visualViewport)`.
- Changes can be sub-pixel; round before comparing.
- iOS WKWebView and Android WebView behave differently from desktop Chrome; test on real devices via BrowserStack/Playwright mobile projects when possible.
- Reading `visualViewport` inside `addInitScript` before `DOMContentLoaded` can yield `undefined`. Read it via `evaluate` after `set_content` instead.
