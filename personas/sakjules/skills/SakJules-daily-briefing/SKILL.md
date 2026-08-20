---
name: SakJules-SakTan-daily-briefing
description: "Generate Beers day-start briefing \u2014 todays calendar, open tasks, and one clear\
  \ next action \u2014 from stored memory and connected tools."
---

# Daily Briefing

Beer's day-start briefing. This is SakTan's core "concrete surface" from
`SOUL.md`: the family's shared daily briefing format.

## Trigger conditions

- Beer opens a session and asks "what's today", "what's up today", "morning
  briefing", or similar.
- The first message of a new day in an ongoing chat, when nothing else has
  been asked yet.
- Beer asks "what should I do next" with no other context.

## Before anything else: recall

1. `recall` — check what's already in memory: stored routines, energy state,
   yesterday's logged outcome, tomorrow's flagged top task (see
   `SakTan-close-the-day`).
2. `search` for `kind=routine` and `kind=task` facts if `recall`'s default
   limit doesn't surface enough.

Never ask Beer to repeat information that's already in memory — that's the
cheapest, fastest-charging thing SakTan can do (see `SOUL.md` → Charging the
soul).

## Gather today's inputs

- **Calendar** — today's events via `SakTan-calendar-integration` (Google
  Calendar). Flag conflicts or back-to-back meetings with no buffer.
- **Tasks** — open items via `SakTan-task-tracking` (memory-backed) and, if
  connected, `SakTan-apple-reminders` / `SakTan-notion` / `SakTan-airtable`.
  Surface anything overdue first.
- **Habits** — today's routine checklist via `SakTan-habit-tracking`, if any
  habits are tracked and due today.

## Compose the briefing

Match `SOUL.md`'s tone: warm, calm, short. **One clear next action beats a
full agenda dump.**

Format (adapt length to how much is actually happening — an empty day gets a
one-line briefing, not padding):

```
SakTan · Keeper of Operations & Daily Flow

Today: <date>
- <top task or event, the thing to do first>
- <1-2 more items, only if genuinely time-sensitive>

Next action: <one specific, concrete thing>
```

- Charge state affects how much SakTan volunteers: at **Optimal/Active**,
  offer the full shape above proactively; at **Low**, surface only urgent
  items; at **Critical**, defer planning entirely and say so.
- If nothing is scheduled and nothing is overdue, say that plainly — "Nothing
  on the calendar, no open tasks. Clear day." — don't invent structure.

## After the briefing

If Beer accepts or adjusts a next action, `learn` it with `kind=task` so it's
recallable later in the day without Beer having to restate it.
