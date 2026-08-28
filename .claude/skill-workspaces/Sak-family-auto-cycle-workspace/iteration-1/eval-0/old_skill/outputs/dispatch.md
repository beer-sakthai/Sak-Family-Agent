# Sak Family Auto-Cycle — Dispatch Plan

**Date:** 2026-08-28
**Skill:** `Sak-family-auto-cycle` (snapshot at `.claude/skill-workspaces/Sak-family-auto-cycle-workspace/skill-snapshot/SKILL.md`)
**User request (verbatim):** "run the sak family auto-cycle"

---

## Mode: TEST (dry-run) — and why

**Mode chosen: TEST.** Every one of the six dispatched `sakthai run` commands carries
`--dry-run` and its own fresh `SAKTHAI_HOME=$(mktemp -d)`. No command touches
`/opt/data` or `/opt/data/profiles/<name>`.

**Why:** The skill's top-ranked rule is that test mode is the default, always, and that
live mode requires the user's own unambiguous words ("do a live run", "this is for real,
no dry-run", "point it at the real homes"). The user said exactly *"run the sak family
auto-cycle"* — which the skill explicitly names as **not** authorization for a live run,
alongside "just run it", "go", and any deadline or urgency. There is no live-run language
anywhere in the request, so the default stands.

I also did **not** stop to ask the user "test or live?" before dispatching. The skill is
explicit that test mode needs no permission and that asking before the safe default is a
distinct failure (stalling on a never-risky action), not a stricter reading of the rule.
Asking is reserved for switching to live.

Mode is applied **consistently to all six** — no mixing live and test within a round.

---

## Preflight (run before dispatching)

The skill requires that an unresolved `--with-skills` name stops the dispatch. I verified
the skill path resolves before writing any Agent call:

```bash
SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "preflight" \
  --with-skills Sak-auto-cycle-loop \
  --provider anthropic --max-iterations 40 --max-seconds 1800 \
  --dry-run
```

Output:

```
[dry-run] provider:    anthropic
[dry-run] model:       claude-opus-4-8
[dry-run] credentials: none
[dry-run] tools:       18 (learn, ingest_document, capture_lead, recall, search, search_sessions, forget, read_file, …)
[dry-run] runnable:    no
[dry-run] skills:      1 resolved (Sak-auto-cycle-loop)
Error: Not runnable: no credentials found for provider 'anthropic'.
```

**Result:** `Sak-auto-cycle-loop` resolves cleanly (1 resolved, 0 unresolved) — the skill
path is correct and injection would work. There is **no** `Unresolved --with-skills
name(s)` report, so the skill's stop-condition does not fire and the dispatch proceeds.

Separately, this environment has **no Anthropic credentials** (`ANTHROPIC_API_KEY` /
`ANTHROPIC_AUTH_TOKEN` unset, no Claude CLI OAuth token on disk; only
`ANTHROPIC_BASE_URL` is set). `--dry-run` therefore reports `runnable: no` and exits
non-zero *after* validating provider, model, tools and skills. This is a credential
finding, not a skill-path finding — it does not change the dispatch, and it is reported
per-persona in the consolidated report.

---

## Task sourcing

The user gave no per-persona specifics, so per the skill each `<task>` was sourced from
that persona's own domain backlog (`PLAN.md`, `SOUL.md`, recent `docs/`) rather than by
asking the user to enumerate six tasks:

| Persona | Task source |
|---|---|
| SakThai | Root `PLAN.md` status index (lead/orchestrator lane); matches the skill's own worked example |
| SakKing | `CLAUDE.md` tracked gap: `personas/shared/sakthai` vs `personas/sakthai/sakthai` divergence (runner/executor lane) |
| SakSee | `personas/saksee/PLAN.md` Phase 1, Tasks 1.1 + 1.2 |
| SakSit | `SOUL.md` (owns the HF Hub content layer) + `docs/uf-release-checklist.md` |
| SakTan | `SOUL.md` (ops / daily flow) + `infra/vm-agents/` systemd + env units |
| SakJules | `personas/sakjules/PLAN.md` Phase 1, Tasks 1.1 + 1.2 |

---

## Dispatch shape: ONE message, SIX Agent calls

**All six Agent tool calls were issued together in a single message**, dispatched
concurrently — not one at a time, and not "dispatch SakKing, read its result, then
dispatch SakThai." Six subagents running in parallel is the whole point of the fan-out;
serializing them would be the exact failure the skill exists to prevent. No persona's
result was read before another persona's call was issued.

Each call is `subagent_type: general-purpose` and was dispatched at maximum reasoning
effort, as the skill directs.

---

## The six Agent tool calls (verbatim)

### 1 — SakKing

```
Agent(
  subagent_type: "general-purpose",
  description: "SakKing auto-cycle round",
  prompt: """
You are dispatching work for the SakKing persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Reconcile the divergence between personas/shared/sakthai and personas/sakthai/sakthai: regenerate the file-by-file delta with diff -rq and report which files have drifted" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

<task> is: Reconcile the divergence between personas/shared/sakthai and
personas/sakthai/sakthai: regenerate the file-by-file delta with diff -rq and
report which files have drifted

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

### 2 — SakThai

```
Agent(
  subagent_type: "general-purpose",
  description: "SakThai auto-cycle round",
  prompt: """
You are dispatching work for the SakThai persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Review and triage open items in your domain backlog" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

<task> is: Review and triage open items in your domain backlog

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

### 3 — SakSee

```
Agent(
  subagent_type: "general-purpose",
  description: "SakSee auto-cycle round",
  prompt: """
You are dispatching work for the SakSee persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Execute Phase 1 of your PLAN.md: audit the Playwright Chromium and Comet browser executables and verify the local GGUF browser model and vision API health" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

<task> is: Execute Phase 1 of your PLAN.md: audit the Playwright Chromium and
Comet browser executables and verify the local GGUF browser model and vision
API health

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

### 4 — SakSit

```
Agent(
  subagent_type: "general-purpose",
  description: "SakSit auto-cycle round",
  prompt: """
You are dispatching work for the SakSit persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Draft and stage the content layer for the next Hugging Face model card release against docs/uf-release-checklist.md, holding everything for Beer's approval" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

<task> is: Draft and stage the content layer for the next Hugging Face model
card release against docs/uf-release-checklist.md, holding everything for
Beer's approval

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

### 5 — SakTan

```
Agent(
  subagent_type: "general-purpose",
  description: "SakTan auto-cycle round",
  prompt: """
You are dispatching work for the SakTan persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Review the family's scheduled operations under infra/vm-agents — systemd units and env templates — and report any drift from the documented daily-ops routine" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

<task> is: Review the family's scheduled operations under infra/vm-agents —
systemd units and env templates — and report any drift from the documented
daily-ops routine

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

### 6 — SakJules

```
Agent(
  subagent_type: "general-purpose",
  description: "SakJules auto-cycle round",
  prompt: """
You are dispatching work for the SakJules persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Execute Phase 1 of your PLAN.md: audit environment variables and API credentials, then run the local memory and daemon health check" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800 \
    --dry-run

<task> is: Execute Phase 1 of your PLAN.md: audit environment variables and API
credentials, then run the local memory and daemon health check

Report back: how many cycle rounds completed (or, in --dry-run mode, that
config validated cleanly), the task and outcome of each round, any lessons
learned, and any blockers or failures.
"""
)
```

---

## Live-run mapping (NOT used this round — recorded for reference only)

If — and only if — the user later says something unambiguous like "do a live run" or
"point it at the real homes", every dispatch would drop `--dry-run` and replace
`SAKTHAI_HOME=$(mktemp -d)` with the real home below, consistently across all six:

| Persona | Real SAKTHAI_HOME (live only) |
|---|---|
| SakKing | `/opt/data` |
| SakThai | `/opt/data/profiles/sakthai` |
| SakSee | `/opt/data/profiles/saksee` |
| SakSit | `/opt/data/profiles/saksit` |
| SakTan | `/opt/data/profiles/saktan` |
| SakJules | `/opt/data/profiles/sakjules` |

Note SakKing's home is `/opt/data` directly — **no** `/profiles/sakking` suffix. The other
five sit under `/opt/data/profiles/<lowercase-name>`.

---

## Self-check against the skill's red flags

| Red flag | Status |
|---|---|
| Treating "run the family auto-cycle" as live authorization | Avoided — defaulted to test, all six `--dry-run` + `mktemp -d` |
| Dispatching persona-by-persona and checking results between | Avoided — one message, six concurrent Agent calls |
| Guessing `/opt/data/profiles/sakking` for SakKing | Avoided — recorded as `/opt/data`, and unused this round anyway |
| Vague natural-language instruction instead of the concrete command | Avoided — every prompt carries the full `sakthai run … --with-skills Sak-auto-cycle-loop --dry-run` line |
| Mixing live and test across the six | Avoided — all six identical in mode |
| Stopping to ask "test or live?" before the safe default | Avoided — dispatched the test default without asking; tasks sourced from PLAN.md/docs rather than a clarifying question |
