---
name: SakTan-habit-tracking
description: Track recurring habits and routines over time in memory, and report consistency rather
  than just todays status.
...
---

# Habit Tracking

A habit is a *recurring* routine Beer wants kept — distinct from a one-off
task (`SakTan-task-tracking`). The value of tracking a habit is in the
pattern over time, not any single day's check-in.

## Defining a habit

When Beer says they want to build or track a routine ("I want to track
X daily/weekly"), record it once as the habit definition:

```
learn(value="habit: <name> — <cadence, e.g. daily / weekdays / weekly>", kind="habit-def", key="<slug>")
```

Don't redefine the same habit every time it's checked in — define once,
log occurrences separately (below).

## Logging an occurrence

Each time Beer reports doing (or skipping) the habit:

```
learn(value="<slug> — <done|skipped> — <date, and a one-line note if relevant>", kind="habit-log", key="<slug>")
```

Keep the note brief — habit logs accumulate fast; a one-line note is enough
context for a later consistency read.

## Reporting consistency

When Beer asks "how am I doing with X" or as part of `SakTan-weekly-review`:

1. `search(query="<slug>")` to pull all `habit-log` entries for that habit.
2. Compute a simple consistency read over the relevant window (e.g. "5 of the
   last 7 days" for a daily habit) — don't just report today's status.
3. Lead with the pattern, not a single data point: "You've kept this 5 of the
   last 7 days" beats "you did it today."

## Tone

Per `SOUL.md`: **honest about capacity**, never a guilt trip. A missed day is
a data point, not a failure to narrate. If consistency has genuinely dropped,
say so plainly and once — then move to what's next, not a lecture.

## Pitfalls

- Don't invent a consistency percentage from fewer than 3 logged occurrences
  — say there's not enough data yet instead of a misleadingly precise number.
- A habit definition without any logged occurrences yet is not "0%
  consistent" — it's simply not started; say that instead.
