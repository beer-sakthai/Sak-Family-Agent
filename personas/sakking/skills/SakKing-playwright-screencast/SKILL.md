---
name: SakKing-playwright-screencast
category: dogfood
description: Use Playwright’s built-in Screencast API (page.screencast) to record
  browser sessions as video, add chapter markers and action annotations, extract frames
  for AI vision, and produce verifiable “video receipts” for agent actions in cron/CI.
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
    source: hermes:playwright-screencast
---

# Playwright Screencast Recording for Browser Automation

## Problem

Headless browser evals leave behind only static screenshots, log text, or trace.zip files. For AI agent browser workflows and cron/CI runs, engineers and reviewers need verifiable video evidence of what the browser actually rendered during a session — not just the final state, but the full sequence of interactions, overlays, and context. Playwright v1.59+ ships the Screencast API (`page.screencast`) to fill that gap, enabling programmatic start/stop recording, chapter markers, action annotations, and per-frame capture.

## When to Use

- You need a verifiable “video receipt” of an agent-driven browser flow for code review or audit
- You want to attach short failure videos to CI reports instead of 200-line trace dumps
- You want to narrate a multi-step flow with chapter overlays for stakeholders
- You need to extract individual JPEG frames from a running session for AI vision input
- You want targeted recordings (skip setup/teardown) rather than full-session capture

## Prerequisite

Playwright >= 1.59. Earlier versions support config-based `video: 'on'` recording only.

## Core Capabilities

### 1. Mid-Test Video Recording with `page.screencast.start()` / `stop()`

The programmatic API controls recording precisely around the code you care about.

```python
await page.screencast.start({
  path: 'artifacts/checkout.webm',
  size: {'width': 1280, 'height': 720},
  quality: 80,
  # Optional: save per-frame JPEGs to callback instead
  # onFrame: lambda frame: save_frame(frame.data, frame.timestamp),
})
await page.locator('#add-to-cart').click()
await page.locator('#checkout').click()
await page.screencast.stop()
```

Key options:
- `path`: where the `.webm` file lands. If omitted, only the frame callback runs.
- `size`: box recorded frames to a fixed viewport box; default scales to 800×800.
- `quality`: JPEG frame quality 0–100; lower values reduce file size at the cost of visible compression.

### 2. Chapter Markers with `page.screencast.addChapter()`

Mark logical sections of a session (login, search, checkout, confirmation) so reviewers can jump through the video.

```python
await page.screencast.addChapter('Login', {description: 'OAuth redirect + form fill'})
await page.getByLabel('Email').fill('agent@example.com')
await page.getByLabel('Password').fill('••••••')
await page.screencast.addChapter('Dashboard Load')
```

Chapters render as a timestamped, centered overlay in the video and persist in the final WebM file.

### 3. Action Annotations with `page.screencast.annotate()` / `showActions()`

Annotate specific actions so the viewer sees what was clicked, typed, or selected — critical for “video receipts” used in code review.

```python
await page.screencast.showActions({position: 'top-left', fontSize: 20})
await page.getByRole('button', {name: 'Submit'}).click()
# Or add a single annotation manually:
await page.screencast.annotate({type: 'action', label: 'Clicked Submit'})
```

Options:
- `fontSize`: text size in pixels.
- `position`: one of `top-left`, `top`, `top-right`, `bottom-left`, `bottom`, `bottom-right`.

Disable cursor decoration in v1.61+ with `cursor: 'none'`.

### 4. Frame Capture for AI Vision Workflows

Use the `onFrame` callback to receive live JPEG frames alongside a file recording, or as the only capture mode when you don’t need a final video.

```python
frames = []
await page.screencast.start({
  size: {'width': 1280, 'height': 720},
  onFrame: (frame) => {
    frames.append({
      'bytes': frame.data,
      'timestamp': frame.timestamp,
      'viewportWidth': frame.viewportWidth,
      'viewportHeight': frame.viewportHeight,
    })
  },
})
# ... agent logic ...
await page.screencast.stop()
```

Use this to stream page state to a vision model during a session without writing a full video to disk.

### 5. CI-Friendly Artifacts and Retention

A 5-minute session at 15 FPS can generate 50–100MB. Keep cron/debug variants brief and set retention policies.

Naming pattern:

```python
import datetime
run_tag = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
await page.screencast.start({
  path: f'artifacts/{run_tag}-agent-session.webm',
  size: {'width': 1024, 'height': 768},
})
```

Post-run:
- Upload WebM to the same artifact store as `trace.zip`, screenshots, and HAR files
- Drop a one-line summary into the CI Job Artifacts metadata so reviewers know the video exists
- For short flows, prefer mid-test recording over recording the entire test

## Relationship to Other Playwright Skills

- **playwright-chromium-tracing** covers `trace.zip` for DOM/network/time-travel debugging. Screencast is orthogonal: it covers visual evidence, chapter narration, and video review.
- **playwright-trace-har-bundle** covers packaging multiple artifacts together.
- Screencast output is best paired with a trace bundle so a reviewer can watch the video and open the trace side-by-side.

## Anti-Patterns

- Do not use screencast as a substitute for visual regression testing (`toHaveScreenshot()`); screencast frames are compressed and not pixel-accurate.
- Do not leave `page.screencast.start()` running across long setup/teardown blocks — only record the scene under inspection.
- Do not assume a 0-byte WebM means “silent success” — it often means the context was never closed or stop() was skipped.
- Avoid high-resolution frame capture on memory-constrained CI runners; cap viewport size and use lower quality.
- Do not store screencasts containing secrets in public artifact stores.

## Verification

1. Run a recorded flow and confirm the `.webm` file is written after `stop()` / context close.
2. Open the file in a local player and confirm chapters and action overlays render.
3. Confirm `onFrame` callback receives frames with increasing timestamps during a 5-second recording.
4. Confirm file size scales with FPS/quality settings.
