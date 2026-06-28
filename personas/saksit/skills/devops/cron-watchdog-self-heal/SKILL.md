---
name: cron-watchdog-self-heal
description: Self-healing watchdog for Hermes cron jobs — re-enables previously-healthy jobs that have been disabled. Use when cron fleet entries drift into a disabled state unexpectedly.
---

# Cron Watchdog Self-Heal

Watch the cron fleet for jobs that were previously `enabled` and healthy but are now `disabled`, then re-enable them. Keep this lightweight: it’s meant to fight drift, not rewrite schedules.

## When to use it

- A cron job disappears from the active roster without human action
- Repeated restarts or profile migrations leave jobs orphaned/disabled
- You want a safety net so scheduled learning/heartbeat jobs come back automatically

## Safety rules

- Only touch jobs that were enabled before — never convert an intentionally disabled job back on
- Avoid infinite re-enable loops: if the same job flips disabled twice within 10 minutes, pause and alert rather than re-enabling again
- Never modify another profile’s cron jobs unless the user explicitly approves cross-profile changes

## Workflow

1. List current jobs: `cronjob` `action=list`
2. Compare against the last known healthy snapshot (if you maintain one) or inspect the `status` / `enabled` flags in the listing
3. For each job that was healthy and is now disabled:
   - Verify no recent user message asked to pause/delete it (check recent session context if needed)
   - Re-enable: `cronjob` `action=resume` `job_id=<id>`
4. Log each action: what was re-enabled, from what prior state, and when
5. If nothing needs healing, stay silent (watchdog pattern)

## Minimal self-heal cron prompt

If you’re scheduling this as a cron job itself, use a tight prompt like:

```
Watchdog: inspect all cron jobs, re-enable any that were healthy and are now disabled.
Run silently when nothing to report.
```

Pair with `no_agent=true` if you instead want the script to run via `cronjob` and only emit output when it actually does something.

## Related

- `cron-fleet-selfheal` — a concrete job ID often used for this pattern
- `hermes-agent` skill — for cron config mechanics and CLI behaviour
