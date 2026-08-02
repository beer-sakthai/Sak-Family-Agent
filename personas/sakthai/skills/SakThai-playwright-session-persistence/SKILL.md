---
name: SakThai-playwright-session-persistence
category: dogfood
description: Reuse authenticated Playwright browser sessions across cron/CI runs using
  storage state, context cookies, and controlled session handoffs.
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
    source: hermes:playwright-session-persistence
---

# Playwright Session Persistence for Scheduled Browser Workflows

## Problem

Automated browser jobs in CI/cron often re-authenticate every run, which adds latency, breaks MFA/captcha barriers, and increases rate-limit risk. Playwright can persist and restore sessions via storage state + cookies, but most guidance only mentions the API calls; this skill documents a reliable session-handoff pattern that survives shell restarts and avoids leaking credentials.

## When to Use

- Cron / workflow jobs that must visit authenticated pages repeatedly
- Tests that need a consistent logged-in state without running login UI every time
- Multi-bot or multi-user QA setups where you want isolated browser contexts but shared auth tokens

## Core Capabilities

### 1. Capture Storage State After Auth

```python
state = await context.storage_state(path=".auth/storage.json")
```

Store the file outside `tmp/` so it survives `pytest --browser-channel=chromium` cleanup or container restarts. Group auth state by project, not by run.

### 2. Restore With Cookies for Provider Isolation

```python
context = await browser.new_context(
  storage_state=".auth/storage.json",
  user_agent="qa-bot/1.0 (+https://example.com/bot)",
  java_script_enabled=True,
)
```

Use a constant `user_agent` so cookie/anti-bot fingerprints do not change between sessions.

### 3. Refresh When State Becomes Stale

Detect stale sessions with a lightweight probe before executing heavy flows:

```python
async def session_ok(context):
  page = await context.new_page()
  await page.goto("https://app.example.com/account/me", wait_until="domcontentloaded")
  ok = await page.locator("text=Payouts").count() > 0
  await page.close()
  return ok
```

If false, rerun a one-time login page and overwrite `storage.json`. Do not delete the old state until the new one succeeds.

### 4. Hand Off Between Unrelated Jobs

For chained jobs in CI (`lint -> auth -> smoke`), export the path through an env var:

```
PLAYWRIGHT_STATE_PATH=.auth/storage.json
```

Avoid secret values in storage state; secrets should live in env variables and be provisioned by CI, not in browser cookies.

### 5. Handle Expiry and Rotation Gracefully

When you detect a 401/redirect-to-login mid-run:

1. Open a fresh private context for login.
2. Complete MFA or captcha.
3. Save new state to the same path.
4. Resume the original context from the updated file.

This keeps long-running autonomous flows resilient.

## Anti-Patterns

- Don’t share the same `storage.json` between human QA and bot sessions; isolate by app role.
- Don’t delete state on every run; treat it as a first-class artifact.
- Don’t rely on storage state alone for products that invalidate tokens server-side — pair with the refresh probe above.

## Verification

After applying this pattern:
1. Run a cron job twice without auth UI.
2. Confirm the second run skips the login flow via a headless console marker or log line.
3. Confirm storage file path outside temp directories.
4. Re-run after state expiry; confirm the fallback login path rebuilds state automatically.
