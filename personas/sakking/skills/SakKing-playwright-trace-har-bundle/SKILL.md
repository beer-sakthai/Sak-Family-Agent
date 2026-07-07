---
name: SakKing-playwright-trace-har-bundle
category: dogfood
description: Package Playwright traces and HAR recordings into verifiable QA bundles
  for cron/CI runs, with CLI inspection commands and headless-safe artifact delivery.
version: 1.0.0
platforms:
- linux
- macos
- windows
metadata:
  sakthai:
    tags:
    - hermes
    - dogfood
    related_skills: []
    source: hermes:playwright-trace-har-bundle
---

# Playwright Trace + HAR Bundles for Offline QA

## Problem

Headless cron/CI runs need inspectable, self-contained browser evidence: not just an error code, but a replayable archive anyone can open without re-running live. Playwright 1.60+ added `tracing.startHar()`/`stopHar()` as first-class tracing APIs, 1.61 added WebSocket requests into HAR/trace recordings, and the CLI gained `playwright show-trace`, `playwright trace actions --grep`, and HTML reporter `.zip` attachments. This skill strings those pieces together into a repeatable bundle pipeline.

## When to Use

- QA jobs that must surface browser QA evidence in GitHub issues or Slack
- Deterministic replay without network access
- Compliant audit evidence where a headless run must still be human-readable
- Reducing debug turnaround: attach a single artifact instead of asking someone to rerun

## Core Capabilities

### 1. Emit Trace + HAR Together

Prefer a single context setup that collects everything at once, so timestamps and actions align.

```js
const context = await browser.newContext();
await context.tracing.start({
  screenshots: true,
  snapshots: true,
});
const har = await context.tracing.startHar('journey.har', { content: 'attach', mode: 'minimal' });
const page = await context.newPage();
// ... automation ...
await context.tracing.stop();
await browser.close();
```

Using `content: 'attach'` embeds content bodies in the HAR for offline readability.

### 2. Name Artifacts with Stable Job Keys

Sorted, traceable filenames survive log rotation and make attributing issues trivial.

```python
import datetime
base = f"artifacts/{datetime.date.today().isoformat()}-job-42"
# => artifacts/2026-06-16-job-42.trace.zip
# => artifacts/2026-06-16-job-42.har
```

Group traces/HARs under a dedicated directory excluded from unrelated caches.

### 3. Inspect Without Re-running

Use the shipped CLI tooling to validate contents before delivery.

```bash
playwright show-trace artifacts/2026-06-16-job-42.trace.zip
playwright trace actions \
  artifacts/2026-06-16-job-42.trace.zip \
  --grep "click|submit"
```

On headless CI, pipe screenshot extracts to PNG or generate a tiny static index.

### 4. Deliver a Bundle for Humans and Agents

Convert the HTML reporter to `.zip` or pair trace + HAR into one compressed archive.

```bash
zip qa-bundle-20260616.zip \
  artifacts/2026-06-16-job-42.trace.zip \
  artifacts/2026-06-16-job-42.har \
  artifacts/failure-1234.png \
  run-summary.md
```

The `.zip` can be uploaded directly to GitHub issues; Playwright renders trace and HAR natively in the web viewer and IDE extensions.

### 5. Use Trace Actions for Regression Signal Extraction

Extract regression-relevant signals without opening a GUI by filtering trace actions.

```bash
playwright trace actions \
  --grep "api|submit|success" \
  run-summary.json \
  | jq '.actions[] | select(.type=="click")'
```

This supports “auto-triage” style reports: the job produces a JSONL/SHA256 manifest of click/assert sequences plus timing, enabling lightweight agent review of many runs.

## Workflow Integration

- Trigger from the same cron is `playwright-chromium-tracing`, but this skill adds offline bundling for delivery.
- Pair with `playwright-network-reliability` to keep the recorded surface focused on application traffic.
- Output `.zip` bundles are web-uploadable to GitHub/Gitea without extracting.
- Keep bundles under size limits; use HAR `mode: 'minimal'` and trace `screenshots: 'on-failure'` to trim bloat.

## Anti-Patterns

- Don’t omit HAR content (`content: 'omit'`) if humans need offline inspection; they’ll have no bodies to read.
- Don’t bundle secrets — the trace/HAR can contain form fields, OAuth query params, and cookies.
- Don’t leave tracing on success runs where screenshots never get inspected; replace with `recordVideo` if you only need failure evidence.

## Verification

1. Run the bundle-producing job and confirm a `.zip` exists with both `.trace.zip` and `.har` entries.
2. Open with `playwright show-trace ...` and confirm actions + network appear.
3. Upload to a GitHub issue draft and confirm preview renders in the web viewer.
4. Use `playwright trace actions --grep <action>` and confirm meaningful actions can be listed.
