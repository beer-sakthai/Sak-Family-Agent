---
name: Sak-auto-cycle-loop
category: cycle
description: >-
  Sustain up to 3 Dream-through-Growth cycle rounds in a single `sakthai run`
  session instead of stopping after the first Growth. Use when a persona
  should keep working through follow-on tasks, each getting its own full
  6-stage cycle, capped at an exact, tracked count of 3 rounds.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - cycle
      - shared
      - auto-cycle
      - multi-round
    related_skills: []
---

# Sak-auto-cycle-loop

Extends the six-stage cycle (Dream through Growth) with one rule: **completing Growth is not the end of
the session by default.** Without this skill, the natural instinct is to
treat "cycle finished" as "task finished" and stop. That instinct is wrong
when this skill is loaded — the session keeps going until the round cap or
the run's own `--max-iterations`/`--max-seconds` budget is spent, whichever
comes first.

## The cap is a count you track, not a feeling you infer

**Hard cap: exactly 3 rounds per invocation. Not "a couple more," not "1-2
items," not "as many as the budget allows" — 3.**

This number is fixed by this skill, not something you estimate from how much
`--max-iterations`/`--max-seconds` budget looks like it has left, and not
something you decide informally in the moment. "I have plenty of budget, so
I'll tackle a few more things" is the failure mode this skill exists to
prevent, even when it sounds reasonable. Budget is a separate, outer
constraint (see below) — it never sets or raises the round cap.

Maintain a literal counter, starting at 1 for the task you were invoked
with. Every time you finish Growth's `sakthai learn --tag growth`, that
round is done — state which round number just completed and how many
remain, out loud, before you decide what to do next. If you're ever unsure
which round you're on, that uncertainty itself is a signal to stop and
recount rather than guess.

### Example: correct round-tracking narration

```
Round 1 of 3 complete: "audit the pricing page copy for accuracy" — lesson
recorded via `sakthai learn --tag growth`. 2 rounds remain. Recalling memory
for the next most valuable pending item before starting Round 2.

... (Dream through Growth on the next item) ...

Round 2 of 3 complete: "fix broken checkout redirect" — lesson recorded.
1 round remains. Starting Round 3.

... (Dream through Growth on the next item) ...

Round 3 of 3 complete: "tighten onboarding email copy" — lesson recorded.
0 rounds remain — this was the last one. Stopping here regardless of
remaining budget. Summary: [round 1 outcome], [round 2 outcome], [round 3
outcome].
```

| After round | Action |
|---|---|
| 1 or 2 | State "Round N of 3 complete, M remain," then `sakthai cycle next` (Growth -> Dream) and start the next round immediately. Do not ask for permission to continue — continuing is the default behavior this skill exists to provide. |
| 3 | State "Round 3 of 3 complete, 0 remain." Stop. Do not call `cycle next` again, and do not start a 4th round for any reason, including leftover budget. Summarize all 3 rounds (one line each: task, outcome, key lesson) and end the session. |

## What "the next round" means

You were given exactly one task at invocation. Round 1 works that task.
Rounds 2 and 3 do **not** require a new task string from outside — Dream's
job is to find it: `sakthai recall` your own memory and any pending
items (PLAN.md, kanban, prior `learn --tag decision` notes) and pick the
single most valuable next thing, the same way a persona's own Dream-stage
skill already instructs. If genuinely nothing useful turns up, that counts as an early
stop: say so, don't invent busywork, and end the session below 3 rounds —
state which round you stopped at and why, using the same "Round N of 3"
phrasing so it's clear the cap wasn't the reason you stopped.

## The outer budget still governs

`--max-iterations` and `--max-seconds` (set by whoever invoked `sakthai
run`) are a hard ceiling *underneath* the 3-round cap, never a reason to
push past it. If either would be exceeded mid-round, stop where you are —
finish the current stage's in-flight action, do not start a new stage, and
summarize progress so far. Never let round-continuation push past the
budget the caller set, and never treat spare budget as license to exceed
round 3.

## Red flags — you are about to violate this skill

- Finishing Growth and ending the session without stating your round count
  ("Round N of 3") first.
- Starting a 4th round because "there's still budget left" — budget is the
  outer ceiling, not license to exceed the round cap.
- Picking an ad hoc number of rounds ("I'll do 1-2 more," "a few more
  items") instead of the fixed cap of 3. If you catch yourself reasoning
  about how many rounds to run rather than reciting the count, stop and
  re-anchor on "3."
- Inventing a task for round 2/3 that wasn't grounded in recall/PLAN.md/kanban,
  just to have something to do.
- Treating "the user only gave me one task" as a reason to never look at
  what round 2 could be — that's exactly what Dream is for.

## Pitfalls

- **Don't skip `learn --tag growth` before advancing.** The lesson is what
  makes "smarter" in "re-enter Dream, smarter" true — skipping it turns
  round 2 into a repeat of round 1's mistakes.
- **Don't silently reset the round counter.** It's a per-session count, not
  per-stage; re-entering Dream doesn't start you back at round 1.
