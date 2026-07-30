# Cron Schedule Pattern — "Every X" + Self-Limit

## Discovery (2026-07-29)

**Bug:** Finite `repeat=N` with `"once in Xm"` schedule format causes the cron to run only once, then die to `"completed"` state. The `repeat` counter shows `1/N` and never advances.

**Fix:** Use `"every Xm"` + `"forever"` repeat, then self-limit inside the prompt.

## The Pattern

### ❌ Broken (repeat=N + once in)

```python
cronjob(
    action="create",
    schedule="1m",          # normalizes to "once in 1m" — BROKEN
    repeat=5,               # dies after 1 run, shows 1/5
    prompt="explore HF repos"
)
```

### ✅ Working (forever + self-limit)

```python
cronjob(
    action="create",
    schedule="every 1m",    # stays "every 1m" — WORKS
    repeat="forever",       # keeps running
    prompt="""Before doing anything, check if we've done 5 runs.
    If yes → print 'Done' and stop.
    If no  → do work, save counter, report.
    """
)
```

## Self-Limit Strategies

### Option 1: Memory counter

Prompt checks `supermemory_search()` or local counter file to track how many runs completed. After N runs, the prompt returns nothing and stops delivering.

### Option 2: State file

Write run count to `~/profiles/sakthai/cron/output/hf-github-learn-counter.txt`. On each run, read it, increment if < N, skip if >= N.

### Option 3: Delivery silence

After the last real run, the prompt just returns "✅ All N runs complete. Stopping." — the cron keeps running forever but stays silent.

## When to Use

- **Finite batch crons** — any job that should run exactly N times then stop
- **Exploratory crons** — discover-and-report patterns that need a fixed number of iterations
- Avoid this pattern for: recurring health checks, watchdogs, or monitoring — those should use `"every Xm"` + `"forever"` without self-limit
