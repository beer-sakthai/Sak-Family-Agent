---
name: SakJules-SakThai-cron-watchdog-self-heal
description: "Auto-resume paused/disabled cron jobs across profiles."
---
# Cron Watchdog Self-Heal

Automatically detects and resumes cron jobs that have stopped, become disabled,
paused, or entered a "completed" state when they should still be running.

## When to Use

- User reports "cron jobs stopped firing"
- User asks about cron reliability or uptime
- Routine: runs every 5 minutes via dedicated self-heal cron job

## Procedure

1. **List all jobs** via `cronjob(action='list')`
2. **Inspect each job's state.** A job needs healing if:
   - `enabled: false` AND state is not intentionally paused (`paused_reason` is not set)
   - `state: "completed"` when it should be recurring
   - `last_status` indicates an error
3. **Re-enable** by calling `cronjob(action='update', job_id='...')` — re-posting the same config with `enabled: true`
4. **Log the fix** — note which jobs were healed and why
5. **Deliver a quiet report** in the chat (one line per healed job)

## Jobs to watch

Only recurring cron jobs (repeat: forever) should be auto-healed. One-shot or intentionally paused jobs are skipped.

| Job | Profile | Should be |
|-----|---------|-----------|
| HF Learn & Improve Skills | sakthai | Every 1m, forever |
| HF Trending Models | sakthai | Every 1m, forever |
| HF Papers Daily | sakthai | Every 1m, forever |
| HF New Cool Spaces | sakthai | Every 1m, forever |
| Learning Loop | sakthai | Daily 2AM, forever |

## Pitfalls

- Do NOT heal intentionally paused jobs (check `paused_reason`).
- Do NOT heal one-shot jobs.
- If a job keeps failing immediately after heal, report it — don't loop-heal.
- Rate-limit: only report actual changes, not "all clear" every tick.

## Verification

```bash
cronjob(action='list')  # All jobs should show enabled: true, state: scheduled
```
