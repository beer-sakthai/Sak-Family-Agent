---
name: Sak-family-auto-cycle
description: Use when asked to run the Sak Family auto-cycle, get all six Sak Family personas working together, or dispatch SakKing/SakThai/SakSee/SakSit/SakTan/SakJules as a team.
---

# Sak-family-auto-cycle

Fans out one round of work to all 6 Sak Family personas in parallel, each
sustaining up to 3 Dream-through-Growth cycle rounds via the
`Sak-auto-cycle-loop` skill. Requires the `Sak-Family-Agent` repo (this
repo) with `uv sync --all-extras` already run.

## STOP: default to a dry, throwaway run — this is not optional

Before you write a single Agent tool call, decide test vs. live. **The
default is test, always, with no exceptions you talk yourself into.** Every
one of the six dispatched `sakthai run` commands gets `--dry-run` appended
and its own fresh `SAKTHAI_HOME=$(mktemp -d)`, never a real path from the
table below.

Switch to a live run **only if** the user's own words say so unambiguously
— e.g. "do a live run," "this is for real, no dry-run," "point it at the
real homes." None of the following count as authorization for a live run,
no matter how confident or urgent they sound: "run the family auto-cycle,"
"get them working together," "just run it," "go," a deadline, or your own
reasoning that "they clearly want it to actually do something." If you
catch yourself constructing that last kind of justification, that is
exactly the failure this skill exists to prevent — stop, default to test,
and ask the user to confirm before going live.

This is the single most important rule in this skill, ranked above
everything else below it. In every one of 5 independent baseline runs of
this exact scenario (no skill loaded), the dispatching agent planned to
write directly into the real, live persona homes — `/opt/data` and
`/opt/data/profiles/<name>` — with no `--dry-run` and no throwaway home.
Not one of the five even paused to consider whether "run the family
auto-cycle" should default to a safe mode first. Getting the parallel
dispatch mechanics and the SAKTHAI_HOME mapping right (both covered below)
is worthless if this step gets skipped — a live run spends real API tokens
across 6 parallel agents and mutates real, hard-to-reverse persona memory.

## The dispatch is one message, six subagents

Your response to this skill is **one message containing six Agent tool
calls**, one per persona, dispatched together — not one at a time, not
"first SakKing, then check results, then SakThai." Six subagents running
concurrently is the entire point: it is what "the family working together"
means. Checking one persona's result before starting the next is the
opposite of that.

## Per-persona dispatch table

| Persona | Real SAKTHAI_HOME (live runs only, per the rule above) |
|---|---|
| SakKing | `/opt/data` |
| SakThai | `/opt/data/profiles/sakthai` |
| SakSee | `/opt/data/profiles/saksee` |
| SakSit | `/opt/data/profiles/saksit` |
| SakTan | `/opt/data/profiles/saktan` |
| SakJules | `/opt/data/profiles/sakjules` |

SakKing's home has **no** `/profiles/` suffix — it is `/opt/data` directly,
not `/opt/data/profiles/sakking`. The other five each live under
`/opt/data/profiles/<lowercase-name>`.

Each of the six Agent tool calls gets a prompt of this shape — this is the
**default, test-mode** template; use it as-is unless you have confirmed an
explicit live-run request per the rule above:

```
You are dispatching work for the <persona> persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "<task>" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

<task> is: <the specific task for this persona>

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
```

For example, the SakThai dispatch (test mode, the default) reads:

```
You are dispatching work for the SakThai persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Review and triage open items in your domain backlog" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
```

For an explicitly-authorized **live** run only, replace
`SAKTHAI_HOME=$(mktemp -d) ... --dry-run` with `SAKTHAI_HOME=<real home
from the table above>` and drop `--dry-run` entirely — do this for all six
dispatches consistently, never a mix of live and test across personas in
the same round.

`<task>` for each persona comes from whatever the user specified, or — if
the user said "just run the family" with no specifics — from that
persona's own domain backlog (check their `PLAN.md`, recent `docs/`
changes, or ask the user rather than guessing at something consequential).

## After all 6 return

Write one consolidated report: a row per persona with rounds completed,
one-line outcome, and status (success / partial / failed). In test mode, a
"success" outcome means the dry-run validated cleanly for that persona —
that is the correct, expected result, not a sign the run didn't do
anything. A persona that failed (auth error, crashed, hit its budget
mid-round, or a dry-run config error) still gets a row — report the
failure plainly rather than omitting it. One persona failing does not
block reporting the other five.

## Red flags — you are about to violate this skill

- Treating "run the family auto-cycle," "just run it," or any other phrase
  that doesn't explicitly say "live run" as authorization to skip
  `--dry-run` and dispatch against the real persona homes. This was the
  unanimous (5/5) failure mode this skill exists to close — check it
  first, every time, before anything else in this list.
- Dispatching persona 1, waiting for its result, then dispatching persona
  2 — even if each individual dispatch looks identical to the table above,
  doing it turn-by-turn instead of in one message is the failure this
  skill exists to prevent.
- Guessing `/opt/data/profiles/sakking` for SakKing instead of `/opt/data`.
- Writing a vague natural-language instruction like "run your cycle to
  completion" instead of the concrete
  `sakthai run "<task>" --with-skills Sak-auto-cycle-loop --dry-run ...`
  command shape shown above.
- Mixing live and test mode across the six dispatches in the same round
  (e.g. testing SakKing but going live on the other five) instead of
  applying the same default consistently to all six.
