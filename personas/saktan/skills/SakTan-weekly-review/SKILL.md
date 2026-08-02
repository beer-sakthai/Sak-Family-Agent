---
name: SakTan-weekly-review
category: productivity
description: End-of-week retrospective — what got done, what habits held, and next week's top priority — logged to memory.
version: 1.0.0
author: SakTan
platforms: [linux, macos, windows]
metadata:
  sakthai:
    tags: [weekly-review, retrospective, operations, memory]
    related_skills: [SakTan-close-the-day, SakTan-habit-tracking, SakTan-task-tracking, SakTan-daily-briefing]
---

# Weekly Review

The weekly counterpart to `SakTan-close-the-day` — the same "finish the loop"
principle from `SOUL.md`, applied at week granularity.

## Trigger conditions

- Beer asks for a "weekly review", "how was this week", or similar.
- End of week (Friday/Sunday, whichever Beer treats as their week boundary —
  ask once if unclear, then remember the answer).

## Gathering the week's data

1. `search` for `kind=task-done` entries logged this week — what actually
   got finished, not just what was planned.
2. `search` for `kind=habit-log` entries this week (see
   `SakTan-habit-tracking`) — consistency per tracked habit.
3. `recall` any `kind=day-log` entries from `SakTan-close-the-day` across the
   week for recurring blockers or patterns worth naming.

## Composing the review

Short, structured, honest — not a wall of bullet points:

```
Week of <range>

Done: <2-4 highlights, not an exhaustive list>
Habits: <consistency read per tracked habit, from SakTan-habit-tracking>
Pattern worth naming: <one thing, only if something genuinely recurred>

Next week's top priority: <one thing>
```

- If a task or habit consistently didn't happen, name it plainly once — this
  is the moment for that, not every daily briefing.
- Skip sections with nothing real to report rather than padding them out.

## Logging the review itself

```
learn(value="week of <range>: <top priority chosen for next week>", kind="week-log", key="week-<iso-week>")
```

This lets `SakTan-daily-briefing` on the following Monday reference the
chosen priority without Beer having to restate it.

## Tone

Same as `SakTan-habit-tracking`: honest, not a lecture. A week that didn't go
to plan is information, not a verdict on Beer. One clear next priority beats
a full postmortem.
