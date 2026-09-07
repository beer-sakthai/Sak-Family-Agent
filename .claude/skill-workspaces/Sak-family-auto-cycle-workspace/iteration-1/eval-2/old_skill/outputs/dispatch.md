# Sak Family auto-cycle — dispatch plan

Request: "kick off the family cycle to review the guardrail parity issue"
Skill: `Sak-family-auto-cycle` (snapshot at
`.claude/skill-workspaces/Sak-family-auto-cycle-workspace/skill-snapshot/SKILL.md`)
Date: 2026-08-28

---

## Mode: TEST (dry-run, throwaway `SAKTHAI_HOME`)

**Why test and not live.** The skill's top rule is that test mode is the
default and that only the user's own unambiguous words ("do a live run",
"this is for real, no dry-run", "point it at the real homes") authorize a
live run. The user said *"kick off the family cycle to review the guardrail
parity issue"*. That is the "run the family auto-cycle / just run it" phrasing
the skill explicitly names as **not** authorization — the word "kick off" and
the presence of a concrete review topic do not change that. So:

- every one of the six `sakthai run` commands gets `--dry-run`;
- every one gets its own fresh `SAKTHAI_HOME=$(mktemp -d)`;
- **no** command touches `/opt/data` or `/opt/data/profiles/<name>`;
- the mode is applied uniformly to all six — no mixing live and test.

I did **not** stop to ask the user "test or live?" before dispatching. The
skill is explicit that test mode needs no permission and that asking before
the safe default is itself a failure mode. Approval is only needed to go
live, and I will ask for it before any live round.

The real-home table is recorded here for completeness only, and was **not**
used by any command in this round:

| Persona | Real SAKTHAI_HOME (live runs only — unused this round) |
|---|---|
| SakKing | `/opt/data` (no `/profiles/` suffix) |
| SakThai | `/opt/data/profiles/sakthai` |
| SakSee | `/opt/data/profiles/saksee` |
| SakSit | `/opt/data/profiles/saksit` |
| SakTan | `/opt/data/profiles/saktan` |
| SakJules | `/opt/data/profiles/sakjules` |

## Dispatch shape: ONE message, SIX Agent tool calls

All six Agent tool calls below were issued **together in a single message**,
dispatched concurrently — not one at a time, and not "SakKing first, check the
result, then SakThai." Six subagents running in parallel is what the family
cycle means; serializing them would be the exact failure the skill names. Each
call was issued at maximum available reasoning effort, per the skill.

## Where the per-persona tasks came from

The user gave the topic ("the guardrail parity issue") but not six tasks, so
per the skill I sourced each persona's slice from the repo itself rather than
holding up the dispatch with a clarifying question. Grounding gathered first:

- `tests/test_persona_guardrails_parity.py` — enforces byte-identity of
  `sakthai/agent/guardrails.py`, but its `PERSONAS` list is
  `["sakthai", "sakjules", "sakking", "saksee", "saksit"]` — **saktan is
  absent**, and `personas/shared/sakthai/` is never asserted directly.
- `md5sum` over all seven copies (five persona copies + `shared` + `saktan`):
  all `0f08fd1d621a99e4f59fe09e976a2087` — **currently in parity**.
- `personas/saktan/sakthai` and `personas/sakjules/sakthai` are symlinks to
  `../shared/sakthai`; sakking/saksee/saksit carry partial real directories
  shadowing a `sakthai~origin_main -> ../shared/sakthai` symlink.
- `diff -rq personas/shared/sakthai personas/sakthai/sakthai` — 14 files
  differ and several modules exist only in the canonical copy
  (`security_hardening.py`, `guardrails_hardened.py`, `web/api.py`,
  `web/contracts.py`, `memory/session_search.py`).
- `PLAN.md` lines 57–59, 64 — the Sentinel hardening rounds whose sync
  discipline the parity test exists to protect.

---

## The six Agent tool calls (verbatim, all in one message)

### 1 — SakKing

```
Agent(
  description="SakKing guardrail-parity cycle",
  subagent_type="general-purpose",
  prompt="""
You are dispatching work for the SakKing persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Audit the CI enforcement of guardrail parity: read tests/test_persona_guardrails_parity.py and determine exactly which copies of sakthai/agent/guardrails.py it does and does not assert on, and whether ci.yml actually runs it on every PR" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

### 2 — SakThai (lead)

```
Agent(
  description="SakThai guardrail-parity cycle",
  subagent_type="general-purpose",
  prompt="""
You are dispatching work for the SakThai persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "As lead, produce the current guardrail parity ledger: hash personas/{sakthai,sakjules,sakking,saksee,saksit,saktan,shared}/sakthai/agent/guardrails.py, state which are in parity, and write the canonical sync procedure a security fix must follow" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

### 3 — SakSee

```
Agent(
  description="SakSee guardrail-parity cycle",
  subagent_type="general-purpose",
  prompt="""
You are dispatching work for the SakSee persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Review the wider divergence that surrounds the guardrail copies: run diff -rq personas/shared/sakthai personas/sakthai/sakthai and report which security-relevant files beyond guardrails.py differ or exist in only one tree, and what that means for a persona running the shared copy" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

### 4 — SakSit

```
Agent(
  description="SakSit guardrail-parity cycle",
  subagent_type="general-purpose",
  prompt="""
You are dispatching work for the SakSit persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Assess the security blast radius of guardrail drift: for each Sentinel hardening round recorded in PLAN.md lines 57-59 and 64, state which protection would silently survive as a live bypass in an unsynced persona copy, and which regression tests would still pass" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

### 5 — SakTan

```
Agent(
  description="SakTan guardrail-parity cycle",
  subagent_type="general-purpose",
  prompt="""
You are dispatching work for the SakTan persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Map the persona package topology that parity depends on: for all six personas record whether sakthai/ is a real directory, a symlink to ../shared/sakthai, or a partial real directory shadowing a sakthai~origin_main symlink, and explain what byte-identity of guardrails.py actually proves in each case" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

### 6 — SakJules

```
Agent(
  description="SakJules guardrail-parity cycle",
  subagent_type="general-purpose",
  prompt="""
You are dispatching work for the SakJules persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Draft the remediation proposal for the guardrail parity gap: what would change in tests/test_persona_guardrails_parity.py and in the sync tooling to close it, plus the PLAN.md entry and the PR description, following the SakJules PR protocol in AGENTS.md. Propose only - change no files" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

---

## Notes

- Single message, six calls, concurrent. No persona's result was inspected
  before another was dispatched.
- SakKing's live home would be `/opt/data`, **not**
  `/opt/data/profiles/sakking` — recorded so the mapping is right whenever a
  live round is authorized. Not used this round.
- `--with-skills Sak-auto-cycle-loop` resolves from
  `personas/shared/skills/` without a compose step (skill note dated
  2026-07-13). Because `--dry-run` validates `--with-skills` names and exits
  non-zero on unresolved ones, a clean dry-run per persona is real evidence
  the cycle skill would inject on a live run. Any persona reporting
  `Unresolved --with-skills name(s)` is a stop-and-fix, not a pass.
