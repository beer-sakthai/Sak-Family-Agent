---
name: SakSee-chrome-devtools
description: Chrome DevTools Protocol (CDP) with Playwright: network interception, tracing, performance profiling, browser introspection. Uses Playwright's CDPSession for protocol-level control.
category: browser
tags: [cdp, chrome-devtools, network, tracing, performance]
---

# Chrome DevTools Protocol (CDP)

Access Chrome DevTools Protocol via Playwright's CDPSession. Provides low-level browser control: network interception, tracing, performance metrics, and DOM introspection.

## When CDP is the Right Choice

| Task | Tool |
|------|------|
| Intercept/modify requests/responses | ✅ CDP Network Domain |
| Performance metrics & traces | ✅ CDP Performance/Tracing |
| Browser-level events | ✅ CDP |
| High-level page interaction | ❌ Use Playwright (page.click, etc.) |
| Screenshots | ❌ Use Playwright (page.screenshot) |

## Setup

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    
    # Create CDP session
    cdp = page.context.new_cdp_session(page)
    
    # Now you can send CDP commands
    cdp.send('Network.enable')
```