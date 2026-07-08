# Sak Family Auto-Cycle — Design

## Problem

The 6-stage Dream → Hope → Care → Joy → Trust → Growth cycle
(`sakthai cycle status|next|set|list`) is currently manual and single-track:
one persona, one `sakthai run` invocation, one pass through the cycle, then
it stops. Getting the whole Sak Family (SakKing, SakThai, SakSee, SakSit,
SakTan, SakJules) working together — each sustaining their own cycle across
multiple rounds — requires a human to individually invoke `sakthai run` for
each persona, repeatedly, by hand.

## Goal

Two skills that compose:

1. A persona can sustain multiple Dream→Growth rounds in one `sakthai run`
   invocation instead of stopping after Growth.
2. From a Claude Code session, one command fans out to all 6 personas in
   parallel, each sustaining their own multi-round cycle, bounded so cost
   stays predictable.

## Non-goals

- No changes to the `sakthai` Python package, CLI, or its test suite. Both
  deliverables are `SKILL.md` documents (prompt-injected guidance), not code.
- No new `--max-cycle-rounds` CLI flag. Round-bounding is a documented
  instruction inside the skill text, layered on top of the CLI's existing
  `--max-iterations` / `--max-seconds` hard limits.
- No unbounded/indefinite looping. Every dispatch has a fixed round cap.

## Architecture

```
Claude Code session
  └─ Sak-family-auto-cycle skill (.claude/skills/)
       ├─ Agent(SakKing)  ─┐
       ├─ Agent(SakThai)   │
       ├─ Agent(SakSee)    ├─ all dispatched in ONE message, parallel
       ├─ Agent(SakSit)    │
       ├─ Agent(SakTan)    │
       └─ Agent(SakJules) ─┘
              │  each subagent runs:
              │  SAKTHAI_HOME=<persona home> uv run sakthai run "<task>" \
              │    --with-skills Sak-auto-cycle-loop \
              │    --provider anthropic --max-iterations N --max-seconds M
              ▼
       persona's sakthai run (agent/loop.py)
              │  guided by the injected Sak-auto-cycle-loop skill:
              │  Dream → Hope → Care → Joy → Trust → Growth → (loop, ≤3 rounds) → stop
              ▼
       consolidated report back to the Claude Code orchestrator
```

## Components

### 1. `Sak-auto-cycle-loop` (shared, sakthai-native)

- Path: `personas/shared/skills/Sak-auto-cycle-loop/SKILL.md`
- Name prefix `Sak-` per `docs/skill-naming.md` (shared layer).
- Injected via `sakthai run "<task>" --with-skills Sak-auto-cycle-loop`.
- Behavior: on completing Growth, `learn --tag growth` the round's lesson,
  then call `cycle next` to re-enter Dream and start the next queued task
  instead of ending the session.
- **Round cap: 3.** The skill tracks rounds completed in-session and, after
  the 3rd Growth, stops cleanly (summarizes what was done across all rounds)
  even if `--max-iterations`/`--max-seconds` budget remains.
- `--max-iterations` / `--max-seconds` (existing CLI flags) remain the hard
  safety net beneath the soft 3-round cap — if either is hit first, the
  agent stops mid-round rather than exceeding the budget.

### 2. `Sak-family-auto-cycle` (Claude Code orchestrator)

- Path: `.claude/skills/Sak-family-auto-cycle/SKILL.md`
- Used from a Claude Code session with this repo checked out.
- On invocation, dispatches 6 `Agent` tool calls in a single message (true
  parallelism), one per persona, each at max reasoning effort.
- Per-persona `SAKTHAI_HOME`:

  | Persona | SAKTHAI_HOME |
  |---|---|
  | SakKing | `/opt/data` |
  | SakThai | `/opt/data/profiles/sakthai` |
  | SakSee | `/opt/data/profiles/saksee` |
  | SakSit | `/opt/data/profiles/saksit` |
  | SakTan | `/opt/data/profiles/saktan` |
  | SakJules | `/opt/data/profiles/sakjules` |

- Each subagent's task: run `sakthai run` for that persona with
  `--with-skills Sak-auto-cycle-loop`, then report what it accomplished
  (rounds completed, lessons learned, any blockers).
- The orchestrator does **not** add its own outer loop — round-bounding
  already happens per-persona inside skill 1. "Loop" = the 3 internal
  rounds; "family working together" = the 6-way parallel fan-out.
- After all 6 return, the orchestrator writes one consolidated report:
  per-persona outcome, and any failures called out explicitly.

## Error handling

A persona subagent that fails (auth error, crash, blocked task, hits its
`--max-seconds` mid-round) reports its own failure in the consolidated
summary. One persona failing does not fail the other 5 — the orchestrator
always reports all 6 outcomes, whether success, partial, or failure.

## Testing

Following `superpowers:writing-skills` TDD methodology:

- **RED:** baseline a subagent against realistic prompts *without* either
  skill present — confirm it (a) stops after one Growth instead of
  continuing, and/or (b) dispatches personas sequentially instead of in one
  parallel message, and/or (c) has no bound on rounds. Document the
  rationalizations/behavior verbatim.
- **GREEN:** write minimal skill text addressing exactly those baseline
  failures; re-run the same scenarios and confirm compliance.
- **REFACTOR:** close any new loopholes found (e.g. an agent that "continues
  the cycle" but skips the round cap, or dispatches personas one at a time
  "to be safe").
- All test dispatches use `--dry-run` and a throwaway `SAKTHAI_HOME`
  (`mktemp -d`), matching the existing `run-sakthai-agent-v2` driver
  pattern. **Never** point a test at a real persona home
  (`/opt/data` or `/opt/data/profiles/*`) or omit `--dry-run` — that would
  spend real API tokens and mutate live agent memory.

## Open questions / deferred

- Task selection ("the next queued task" for a persona to Dream about) is
  out of scope here — both skills assume a task is already given to
  `sakthai run "<task>"` by the caller (human or orchestrator). A future
  skill could pull from each persona's own backlog/kanban automatically.
- **Deployment/sync is out of scope, and blocks live use as shipped.**
  `Sak-auto-cycle-loop` lives at `personas/shared/skills/` in this repo,
  which is not on the `sakthai` runtime's skill-discovery path. A live
  `--with-skills Sak-auto-cycle-loop` dispatch will fail to resolve the
  skill until it's composed/synced into each persona's live skill
  directory via make compose-personas (which runs scripts/compose_persona.py /
  skill-mirroring pattern — see docs/skill-naming.md). Flagged in
  `Sak-family-auto-cycle`'s own text so a live-run attempt isn't
  surprised by it, but the actual sync step is a separate task.
