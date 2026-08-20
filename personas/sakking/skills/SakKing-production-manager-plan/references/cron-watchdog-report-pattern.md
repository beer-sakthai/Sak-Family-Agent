# Automated Production Report via Cron Watchdog — Confirmed 2026-07-07

Set up a weekly production metrics report using the cron watchdog pattern (no_agent=True).

## Architecture

```
production_metrics.py (Python script, stdlib only)
        ↓ stdout (non-empty = deliver, empty = silent)
cronjob(no_agent=True, script="production_metrics.py")
        ↓ delivers verbatim to Beer's Telegram
```

## Script Pattern

Create `profiles/saksit/scripts/production_metrics.py`:

```python
#!/usr/bin/env python3
"""Template for production metrics watchdog."""

import json, os, sys
from datetime import datetime, timezone, timedelta

STATE_FILE = os.path.expanduser("~/.production_metrics_state.json")

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def delta(current, previous):
    if previous is None or previous == 0:
        return "first run"
    change = ((current - previous) / previous) * 100
    if abs(change) < 1: return "flat"
    return f"{'up' if change > 0 else 'down'} {change:+.1f}%"

def main():
    now = datetime.now(timezone.utc)
    state = load_state()
    
    # --- Collect metrics ---
    # Use Composio API calls or public endpoints
    # ---
    
    lines = ["Weekly Production Report"]
    lines.append(f"Period: {(now - timedelta(days=7)).strftime('%b %d')} - {now.strftime('%b %d, %Y')}")
    # Add metrics lines...
    
    save_state(state)
    sys.stdout.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    main()
```

## Cron Registration

```python
cronjob(
    action="create",
    name="production_weekly",
    script="production_metrics.py",   # relative to ~/profiles/saksit/scripts/
    no_agent=True,                     # skip LLM, deliver stdout verbatim
    schedule="0 12 * * 0",            # every Sunday at 12:00 UTC
)
```

## Watchdog Semantics (no_agent=True)

| Stdout | Behavior |
|--------|----------|
| Non-empty | Delivered verbatim to Beer's Telegram |
| Empty | Silent — no message sent |
| Non-zero exit or timeout | Error alert sent |

Design the script to stay silent when metrics are stable, deliver only when there's something worth reporting (threshold crossed, new content published, anomaly detected).

## State Persistence

The script tracks state across runs via a JSON file (stdlib only, no external deps):
- `state.json` stores last-known metric values
- Each run compares current vs previous, computes deltas
- Saves updated state for next week's comparison

## Pitfalls

- **First run always shows 0s** — establish baseline, next week's report compares against it
- **Script must use stdlib only** — no pandas, no requests, no external packages
- **YouTube public stats require API key** — use `YOUTUBE_GET_CHANNEL_STATISTICS` via Composio instead for authenticated calls
- **Instagram detailed stats require authenticated Graph API** — watchdog-only script can't do this; mark as "needs agent-run for details"
- **Test the script locally first** before registering the cron: `uv run ~/profiles/saksit/scripts/production_metrics.py`
