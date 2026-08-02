---
name: SakThai-playwright-cross-browser-visual-parity
category: playwright-growth
description: Use Playwright to capture and compare visual output across Chromium,
  Firefox, and WebKit for the same page/state. Detect rendering differences, font
  fallbacks, layout shifts, and viewport quirks by generating baseline and diff screenshots
  in a repeatable script.
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
    source: hermes:playwright-cross-browser-visual-parity
---

# Playwright Cross-Browser Visual Parity

## Purpose

Browser engines render the same HTML/CSS with subtle differences. This skill
gives you a scriptable way to:

- launch Chromium, Firefox, and WebKit in headless mode,
- navigate to the same URL/page state in each,
- capture full-page or viewport screenshots,
- compare pixel deltas and produce quick failure/parity reports,
- store artifacts for review when a difference exceeds a threshold.

Use it for:
- cross-browser regression smoke checks,
- catching WebKit-only or Firefox-only rendering bugs,
- validating that baseline UI changes didn’t break a supported browser,
- generating CI artifacts on cross-browser runs.

---

## Prerequisites

- `playwright` installed and browsers downloaded (`playwright install chromium firefox webkit`).
- Python 3.11+ environment.
- Optional: `Pillow` for diff image composition (`pip install pillow`).
- A reachable page or `data:` URL for smoke testing.
- Disk space for temporary screenshots in CI runs.

Install check:

```bash
python - <<'PY'
try:
    import playwright
    from PIL import Image
    print('playwright + pillow ok')
except Exception as e:
    raise SystemExit('missing dependency: %s' % e)
PY
```

---

## Core workflows (tool calls)

1. **Launch parallel browser contexts**
   - `p.chromium.launch(headless=True)`, `p.firefox.launch(headless=True)`, `p.webkit.launch(headless=True)`.
   - Reuse a single page state by replaying the same navigation sequence or by serializing state to `storageState` and loading it per browser.

2. **Capture screenshots with deterministic viewport**
   - `page.set_viewport_size({"width": 1280, "height": 720})` for each browser before navigation.
   - Use `page.screenshot(path=path, full_page=full_page)` and name files with browser prefix.

3. **Compute pixel-level diff**
   - Load all browser screenshots into `PIL.Image`, convert to RGBA.
   - Optionally align crops or ignore dynamic regions with masks.
   - Produce a diff image and count divergent pixels; fail when ratio exceeds threshold (e.g. >0.1%).

4. **Emit concise report**
   - Print per-browser screenshot path.
   - Print `pass` / `fail` with max delta and affected pixel ratio.
   - Write a JSON summary to stdout for CI parsers.

---

## Minimal proof of concept

Run this from a Python-capable shell with Playwright and Pillow installed:

```bash
python - <<'PY'
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    out_dir = Path('/tmp/playwright-cross-browser-poc')
    out_dir.mkdir(exist_ok=True)
    browsers = ['chromium', 'firefox', 'webkit']
    shots = {}
    async with async_playwright().start() as p:
        for name in browsers:
            browser = await getattr(p, name).launch(headless=True)
            page = await browser.new_page(viewport={"width": 800, "height": 600})
            await page.set_content('<html><body style="font-family: Arial, sans-serif; padding: 24px;"><h1>Hello</h1><p>World</p></body></html>')
            await page.wait_for_load_state('domcontentloaded')
            path = out_dir / f'{name}.png'
            await page.screenshot(path=str(path), full_page=False)
            shots[name] = path
            await browser.close()
    print('screenshots captured:')
    for name, path in shots.items():
        print(f'  {name}: {path} ({path.stat().st_size} bytes)')
    # naive parity check: same size across browsers for this PoC
    sizes = {k: v.stat().st_size for k, v in shots.items()}
    all_same = len(set(sizes.values())) == 1
    print('parity (size-equal heuristic):', 'pass' if all_same else 'fail', sizes)

asyncio.run(main())
PY
```

Expected local outcome:
- PNGs are written to `/tmp/playwright-cross-browser-poc/`.
- In headless CI containers, `webkit` may render fonts differently; the equality heuristic is only illustrative. Replace size comparison with pixel diff logic for real parity checks.

---

## Prerequisites

In addition to the base Playwright runtime requirements:

- Browser binaries available for the matrix, or restricted to the subset your CI supports.
- Clean environment per browser to avoid GPU/driver font differences (headless with `--no-sandbox` in containers).
- For flaky tests, pin zoom/font rendering via `force-device-scale-factor=1` and `--disable-gpu`.

---

## Pitfalls

- Different default fonts between WebKit and Chromium cause false diffs. Use a commonly available font stack and consider overriding with `font-family` on the `<html>` element.
- `full_page=True` can produce wildly different dimensions per engine when scrollbars change size; anchor to fixed viewport in headless CI.
- Screenshot timing matters: capture only after `domcontentloaded` or after explicit animation/await; otherwise you diff during paint/settling.
- Browser binary drift across CI runners: pin Playwright version to avoid engine updates breaking baselines.
- Memory: storing large `full_page` pixels for PR batches can fill disk quickly. Use `full_page=False` and deterministic viewport when possible.
- **Ubuntu 26.04+ browser packaging:** Playwright currently fails with `Executable doesn't exist` / `Playwright does not support chromium on ubuntu26.04-x64` because upstream browser builds lag behind new Ubuntu releases. Workarounds: (1) use `playwright install-deps` first, (2) pin CI to Ubuntu 24.04 or earlier, (3) use `chromium-headless-shell` only where available, or (4) skip cross-browser visual parity on unsupported platforms rather than failing the whole run.

---

## Verification step

Run the cross-browser PoC and inspect the summary:

```bash
python scripts/playwright_cross_browser_parity.py --url https://example.com --viewport 1280x720 --threshold 0.001
```

A non-zero exit code with a one-line reason string means the page rendered differently across engines beyond the allowed threshold.
