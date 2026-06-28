---
name: server-timing-header
description: Use the HTTP Server-Timing response header to expose backend performance metrics to browser developer tools and JavaScript, enabling front-end-to-back-end performance debugging.
version: 1.0.0
author: SakSit
platforms: ["linux", "windows", "macos"]
metadata:
  hermes:
    tags: ["http", "performance", "debugging", "backend", "web-vitals"]
---

# Server-Timing Header

## Concept

`Server-Timing` is an HTTP response header that surfaces backend performance metrics (DB queries, CPU time, cache hits, CDN latency) directly in browser DevTools and via the JavaScript `PerformanceServerTiming` interface. It creates a unified trace from client to server without frontend instrumentation.

## When to Use

- Debugging TTFB or slow API endpoints from the browser
- Correlating backend operations (DB, cache, compute) with user-facing latency
- Sharing performance traces between frontend and backend teams
- Monitoring production performance without custom client-side code

## Syntax

```http
Server-Timing: <metric-name>;dur=<duration-in-ms>;desc="<description>"
```

Multiple metrics are comma-separated:

```http
Server-Timing: db;dur=53, cache;desc="Redis";dur=2.4, app;dur=47.2
```

## Backend Example (Node.js / Express)

```js
app.use((req, res, next) => {
  const start = Date.now();
  res.setHeader('Server-Timing', 'app;dur=0');
  res.on('finish', () => {
    const dur = Date.now() - start;
    res.setHeader('Server-Timing', `app;dur=${dur}`);
  });
  next();
});
```

## Frontend Example (JavaScript)

```js
// Read server timings from the Navigation Timing API
performance.getEntriesByType('navigation')[0].serverTiming
  .forEach(metric => {
    console.log(`${metric.name}: ${metric.duration}ms (${metric.description})`);
  });
```

## Cross-Origin & Security

- By default, metrics are same-origin only
- Use `Timing-Allow-Origin: *` (or specific origins) to expose metrics cross-origin
- **HTTPS required** in some browsers for `PerformanceServerTiming` access
- Do not expose sensitive internal hostnames, credentials, or PII in descriptions

## Why It Matters

Became Baseline Newly available on web.dev (March 2023). It is the fastest path from "the page feels slow" to "the database query took 800ms" — no extra payloads, no adoptation friction, visible directly in DevTools Network tab.

## Source

Extracted from https://web.dev/performance/ and https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Server-Timing
