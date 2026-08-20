---
name: SakKing-core-web-vitals-basics
description: "Core Web Vitals (LCP, CLS, INP): definitions, thresholds, and when to measure them for web performance and SEO."
version: 1.0.0
author: SakSit
license: MIT
platforms: [web]
metadata:
  hermes:
    tags: [performance, web-vitals, ux, seo]
---

# Core Web Vitals Basics

## Concept
Core Web Vitals are three user-centric metrics Google uses to evaluate page experience. They measure loading performance, visual stability, and interactivity.

## Metrics & Thresholds

| Metric | What it measures | Good | Needs improvement | Poor |
|--------|------------------|------|--------------------|------|
| **LCP** (Largest Contentful Paint) | Loading — when the largest content element becomes visible | ≤ 2.5 s | 2.5 s – 4 s | > 4 s |
| **CLS** (Cumulative Layout Shift) | Visual stability — unexpected layout shifts | ≤ 0.1 | 0.1 – 0.25 | > 0.25 |
| **INP** (Interaction to Next Paint) | Responsiveness — latency of all interactions | ≤ 200 ms | 200 ms – 500 ms | > 500 ms |

## When to use
- Before and after performance launches to measure real-user impact
- Debugging UX complaints (“page feels jumpy” = suspect CLS; “feels sluggish” = suspect INP)
- SEO monitoring because Core Web Vitals influence search ranking
- Setting performance budgets in CI or release gates

## Quick measurement snippet
Use the `web-vitals` library to capture field data:

```js
import { onLCP, onCLS, onINP } from 'web-vitals';

onLCP(console.log);
onCLS(console.log);
onINP(console.log);
```

For lab testing, use Chrome DevTools Performance panel or `page.evaluate(() => ...)` in Playwright to snapshot these values during CI runs.

## One-line guardrail
If a release pushes any metric into “Poor,” block or flag the deploy and treat it as a P0 performance bug.
