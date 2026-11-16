---
name: SakSee-web-scraping
version: 1.0.0
description: 3-tier web scraping and extraction escalation workflow for SakSee, minimizing browser memory bloat and Chromium overhead.
category: web-browser
tags:
- web
- scraping
- playwright
- browser
---

# 3-Tier Web Scraping Escalation

To maximize resource efficiency and prevent browser memory bloat on low-memory environments, web scraping follows a strict 3-tier escalation protocol:

## 1. Tier 1 (Fast & Free)
- **Target**: Static web pages, documentation, REST endpoints, raw Markdown, and RSS feeds.
- **Tools**: `curl`, `httpx`, or standard HTTP GET with `BeautifulSoup` / html-to-markdown parsing.
- **Rule**: If content is retrievable via static HTTP GET without JavaScript execution, NEVER spawn a Chromium or browser process.
- **Constraint**: Must enforce a 10s socket timeout and sandbox safety.

## 2. Tier 2 (Render-Only)
- **Target**: Client-side rendered Single-Page Applications (SPAs) or JS-hydrated static pages without user interactions.
- **Tools**: Headless Chromium instance via lightweight render-only CLI with strict `--timeout=15s`.
- **Rule**: Load DOM, wait for network idle (max 5s), dump rendered HTML / markdown snapshot, and immediately reap the process.

## 3. Tier 3 (Interactive Playwright)
- **Target**: Complex multi-step user workflows (login forms, pagination clicks, canvas inspection, auth tokens).
- **Tools**: Full interactive Playwright MCP session (`@playwright/mcp@0.0.83`).
- **Rule**: Reserved exclusively for active user simulation. Never use Tier 3 for simple content scraping.
