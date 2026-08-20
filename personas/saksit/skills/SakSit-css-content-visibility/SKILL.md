---
name: SakSit-css-content-visibility
description: Use CSS content-visibility to skip off-screen rendering and improve page performance.
version: 1.0.0
author: SakSit
platforms: ["linux", "windows", "macos"]
metadata:
  hermes:
    tags: ["css", "performance", "web", "rendering"]
---

# CSS Content-Visibility

## Concept

`content-visibility` is a CSS property that allows the browser to skip rendering work (layout, paint) for elements that are off-screen. This can dramatically improve initial page load and interaction speed, especially on long pages with many sections.

## When to Use

- Long scrolling pages with distinct sections (landing pages, documentation, articles)
- Pages with heavy components below the fold
- Improving Largest Contentful Paint (LCP) and reducing main-thread work
- Any page where off-screen content blocks initial render

## Values

- `auto` — Browser decides; skips rendering if off-screen, resumes when near viewport
- `hidden` — Never renders (good for tabs/accordions)
- `visible` — Default behavior

## Code Example

```css
/* Apply to major page sections */
.section {
  content-visibility: auto;
  /* Optional: Contain intrinsic size to prevent layout shifts */
  contain-intrinsic-size: 1000px;
}
```

```html
<!-- Each section below the fold loads faster -->
<section class="section">
  <h2>Important Feature</h2>
  ...
</section>
```

## Why It Matters

From web.dev: content-visibility became Baseline Newly available in September 2024, meaning it can be safely used across all major browsers without prefixes or fallbacks. It reduces rendering cost by skipping off-screen work until the user scrolls near it.

## Source

Extracted from https://web.dev/performance/ — "Baseline Newly available web performance features" section.