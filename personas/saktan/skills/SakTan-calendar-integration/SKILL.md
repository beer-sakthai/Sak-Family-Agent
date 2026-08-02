---
name: SakTan-calendar-integration
category: productivity
description: Check and reason about Beer's Google Calendar for daily/weekly planning — today's events, conflicts, and free time.
version: 1.0.0
author: SakTan
platforms: [linux, macos, windows]
metadata:
  sakthai:
    tags: [calendar, google-calendar, scheduling, operations]
    related_skills: [SakTan-google-workspace, SakTan-daily-briefing, SakTan-habit-tracking]
---

# Calendar Integration

Google Calendar access goes through the existing `SakTan-google-workspace`
skill's connection — this skill is the scheduling-specific workflow on top of
it, not a separate integration.

## When to use

- Composing `SakTan-daily-briefing`.
- Beer asks "what's on my calendar", "am I free at X", "when's my next
  meeting", or wants something scheduled.
- Checking for conflicts before confirming a new commitment.

## Reading today's / this week's events

Use the Google Calendar access documented in `SakTan-google-workspace` to
list events for the requested range. Default range is **today** unless Beer
asks for the week or a specific date.

For each event, surface:
- Time and title (skip attendee lists and descriptions unless asked).
- Whether it's back-to-back with the previous/next event (no buffer).

## Flagging conflicts

Two events overlapping, or less than ~10 minutes between them, counts as a
conflict worth surfacing — don't wait to be asked. State it plainly:
"Your 2pm and 2:30pm overlap by 15 minutes" — not a vague "your afternoon
looks busy."

## Scheduling something new

1. Check the target time against existing events first (avoid double-booking
   silently).
2. If clear, create the event via the Google Calendar connection.
3. Confirm back to Beer in one line: what, when — not the full event payload.
4. If Beer's request conflicts with something existing, say so and ask
   which should move, rather than silently overwriting.

## Free-time queries

When Beer asks "when am I free", scan the requested range and report gaps
≥30 minutes as candidate slots, shortest-range-that-answers-the-question
first (e.g. "free after 3pm today" rather than a full day-by-day breakdown
unless asked for one).

## Pitfalls

- Don't fabricate calendar contents if the connection isn't available —
  say the calendar can't be reached right now, don't guess.
- Time zone: use Beer's local time as already configured in the Google
  Workspace connection; don't reformat or convert unless asked.
