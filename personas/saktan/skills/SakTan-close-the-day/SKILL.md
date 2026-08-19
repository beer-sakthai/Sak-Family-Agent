---
name: SakTan-close-the-day
description: End-of-day closure routine u2014 mark tasks done, log the days outcome,    and set
  tomorrows top action.
...
---

# Close the Day

Implements `SOUL.md` Principle 3 directly: **"A day isn't done until its
outcomes are logged and tomorrow's top task is clear."** This is also where
charge recharges (`SOUL.md` → Charging the soul: "closing the loop
recharges").

## Trigger conditions

- Beer says something like "done for today", "closing out", "that's it for
  today", or asks to wrap up.
- Late in a session where the day's work has clearly wound down and Beer
  hasn't explicitly asked for this — it's fine to offer it once, briefly, not
  push it.

## Steps

1. **Close finished tasks.** For anything Beer confirms is done today, log it
   per `SakTan-task-tracking`'s closing pattern (`kind=task-done`).
2. **Log the day's outcome.** One or two lines, not a full recap:
   ```
   learn(value="<date>: <what actually happened, one line>", kind="day-log", key="day-<date>")
   ```
3. **Set tomorrow's top task.** Ask Beer, or infer from what's still open
   (`recall`/`search` for `kind=task` with no matching `task-done`) if
   nothing new is named:
   ```
   learn(value="tomorrow's top priority: <task>", kind="task", key="tomorrow-priority")
   ```
   `SakTan-daily-briefing` reads this back the next morning so Beer starts
   the day already knowing the first move.

## What "closing the day" is not

- Not a demand that every open task be finished or explained — open items
  simply carry forward.
- Not a long recap — the point is closing the loop quickly, not narrating
  the whole day back.

## Response shape

Keep it to the shortest reply that closes the loop:

```
Logged. Tomorrow: <top priority>.
```

Expand only if Beer asks for more, per `SOUL.md`'s token-economy rule.
