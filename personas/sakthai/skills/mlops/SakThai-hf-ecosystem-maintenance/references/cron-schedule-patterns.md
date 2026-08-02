# Cron Schedule Patterns — SakThai Fleet

## The Finite Repeat Bug

**Problem:** `"schedule": "1m"` normalizes to `"once in 1m"` system-side. When combined with a finite `repeat=N`, the job runs ONCE then immediately goes to `state: "completed"` with `repeat: "1/N"`. Next run never fires.

**Symptoms in cron list:**
- `"schedule": "once in 1m"` 
- `"repeat": "1/5"` (should be "5 times" or progression)
- `"next_run_at": null`
- `"state": "completed"` after first run

**Fix:** Never use finite `repeat` count with `"schedule": "1m"` (which becomes "once in 1m"). Instead:

1. Use `"schedule": "every 1m"` with `"repeat": "forever"`
2. Add **self-limiting logic** in the prompt: the agent checks a counter (supermemory, counter file, or delivered-message count) and stops executing after N real runs
3. After N runs, the job continues to fire (system won't stop it) but the prompt tells the agent to stay silent

## Working Pattern: "every Xm" + "forever" + Self-Limit

```python
# Cron create pattern that works:
cronjob(
    schedule="every 1m",    # NOT "1m"
    repeat=0,               # 0 = forever (or omit for forever)
    prompt="""...do work... 
    Important: check counter first. If 5 runs done, print nothing and exit."""
)
```

## Working Pattern: no_agent Scripts

For `no_agent=True` script-based jobs:
- Script stdout IS the delivery
- Empty stdout = silent (nothing sent to user)
- Works well for watchdogs: script checks state, outputs only on state change
- Scripts should stay quiet when there's nothing to report

## Self-Heal Pattern

The cron-fleet-selfheal script (`cron-selfheal.py`) reads processes.json and re-enables stopped/errored recurring cron jobs. Runs every 1m silently.
