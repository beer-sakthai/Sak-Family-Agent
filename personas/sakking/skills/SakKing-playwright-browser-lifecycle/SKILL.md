---
name: SakKing-playwright-browser-lifecycle
category: dogfood
description: Manage Playwright browser process lifecycles for long-lived cron/CI flows
  — waitForEvent('close'), controlled abort patterns, detached browser reuse, child-process
  cleanup on timeout, and safe teardown for Chromium launched on ephemeral environments.
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - playwright
    - browser
    - lifecycle
    - cron
    - cleanup
    - hermes
    - dogfood
    related_skills: []
    source: hermes:playwright-browser-lifecycle
---

# Playwright Browser Lifecycle

This skill covers browser-process lifecycle control beyond standard `page`/`context` teardown.

## When to use

- Long cron harvests or audit jobs where a hung page must not leak a browser.
- Runbook scripts that should stop and close the browser on the first missing signal.
- Headless WSL/CI runs where a stray Chromium process blocks the next run.

## 1) Launch with a close handle

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    try:
        closed = browser.wait_for_event("close", timeout=5 * 60_000)  # 5 min
    finally:
        browser.close()
```

If no one calls `browser.close()` within the timeout, the `timeout` exception lets you run a hard kill.

## 2) Hard kill fallback

```python
import shutil, subprocess

def kill_chromium():
    if shutil.which("pkill"):
        subprocess.call(["pkill", "-f", "chrome"])
    else:
        subprocess.call(["taskkill", "/IM", "chrome.exe", "/F"])
```

Use this inside `except` from the `wait_for_event` timeout branch.

## 3) Page-driven abort signal

```python
page = browser.new_page()
page.goto("https://example.com")
page.evaluate("window.stop()")  # abort pending loads on user cancel
browser.close()
```

## 4) Storage state + detached reuse

```python
context = browser.new_context()
# ... do work ...
state = context.storage_state(path="state.json")
context.close()
browser.close()

# Reopen using saved state
context = browser.new_context(storage_state="state.json")
```

## 5) Graceful child-process cleanup on WSL/Ubuntu

- Always wrap `browser.close()` in `try/finally`.
- After the outer `with sync_playwright()` and `browser.close()`, run `pkill -f chromium` once if you saw any `chromium` child still alive.
- Do not rely on `dispose()` alone — it does not terminate the browser process in some headless configurations.

## Pitfalls

- `wait_for_event('close')` docs can be terse; the pattern above is the idiomatic implementation.
- Headless + WSL + Docker-in-Docker forces hard kill fallback — don’t skip it.
- Background browser runs launched with `playwright launch(background=True)` need explicit `process.kill()` in addition to `browser.close()`.

## Checklist

- [ ] Browser wrapped in `try/finally` or `with`
- [ ] `wait_for_event("close", timeout=...)` chosen with the right job cadence
- [ ] Hard kill fallback present on WSL/Docker environments
- [ ] Final `pkill`/`taskkill` only after confirming `browser.close()` returned
