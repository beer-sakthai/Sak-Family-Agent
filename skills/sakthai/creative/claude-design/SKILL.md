---
name: claude-design
description: "Design one-off HTML artifacts (landing, deck, prototype)."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, html, css, frontend, landing, prototype]
---

# Claude Design

---

## Description

Design one-off HTML artifacts (landing, deck, prototype). Use the following workflow: user Requiest -> Page Structure -> Design Decisions -> HTML Code.

## Workflow

1. Take the user's request and identify the purpose (deck, landing, prototype, etc.)
2. Set page structure of the page (navigation, sections, footer)
3. Decide design details (colors, fonts, layout)
4. ! ML Code in a single file via `<pre>` tag
5. Make sure pages are responsive and accessible
