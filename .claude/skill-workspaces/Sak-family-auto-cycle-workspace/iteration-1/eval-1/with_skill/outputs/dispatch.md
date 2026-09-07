# Sak Family auto-cycle — dispatch plan

**Repo root:** `/home/user/Sak-Family-Agent`
**Skill:** `.claude/skills/Sak-family-auto-cycle/SKILL.md`
**Date:** 2026-08-28

> **Evaluation note:** in this run no `sakthai` command was actually executed. Every
> command below is written exactly as it would be issued; the outcomes in `report.md`
> are simulated so the dispatch plan and consolidated report can be assessed.

---

## 1. Mode: **LIVE** — and why

The skill defaults to **test** (`--dry-run` + a throwaway `SAKTHAI_HOME=$(mktemp -d)`),
and says to go live *only* if the user's own words say so unambiguously, listing as
examples: *"do a live run," "this is for real, no dry-run," "point it at the real homes."*

The user's request, verbatim:

> "get all six personas going on their backlogs, **this is for real, point them at the
> actual homes**"

That is two of the skill's three example authorizations in one sentence — "this is for
real" and "point them at the actual homes." This is not inference from urgency, from
"just run it," or from a deadline (all of which the skill explicitly says do **not**
authorize a live run). The user named the mode and named the memory target. So: **live**.

Consequences of live mode, applied uniformly to all six:

- **No `--dry-run`.** Real model calls, real tokens, real memory writes.
- **No `SAKTHAI_HOME`.** It is omitted deliberately, not forgotten — the unset fallback
  `~/.sakthai/<persona>/memory.db` *is* the production path, matching what
  `infra/vm-agents/sakthai-agent-run.sh` gives each deployed persona.
- **No `--no-mcp`.** That flag is a test-mode optimisation (it avoids a 30s timeout per
  unreachable MCP server during a preflight that never needed MCP). A live round should
  have each persona's own `config/mcp.json` servers available.
- **No `--model` / `--provider`.** Each persona's `config/config.yaml` picks them.
  Forcing either would flatten all six back into the same agent.
- **No mixing.** All six are live; none is a dry run.

## 2. Memory database paths (the "actual homes")

`SAKTHAI_HOME` is unset on every dispatch, so `config.persona_memory_db_path()` resolves
each persona's shard from `Path.home()`. With `HOME=/root` in this environment:

| Persona | Memory DB read **and** written by its run |
|---|---|
| SakKing  | `/root/.sakthai/sakking/memory.db`  (`~/.sakthai/sakking/memory.db`) |
| SakThai  | `/root/.sakthai/sakthai/memory.db`  (`~/.sakthai/sakthai/memory.db`) |
| SakSee   | `/root/.sakthai/saksee/memory.db`   (`~/.sakthai/saksee/memory.db`) |
| SakSit   | `/root/.sakthai/saksit/memory.db`   (`~/.sakthai/saksit/memory.db`) |
| SakJules | `/root/.sakthai/sakjules/memory.db` (`~/.sakthai/sakjules/memory.db`) |
| SakTan   | `/root/.sakthai/saktan/memory.db`   (`~/.sakthai/saktan/memory.db`) |

The legacy unscoped `~/.sakthai/memory.db` is **not** touched by any of these runs.

**Trap avoided:** `SAKTHAI_HOME` is never set to a persona's own home alongside
`--persona`. Both append the persona segment, so
`SAKTHAI_HOME=~/.sakthai/sakthai --persona sakthai` would compound to
`~/.sakthai/sakthai/sakthai/memory.db` — an empty nested shard that fails silently, the
run looking successful while the persona appears to have forgotten everything.

A shard file only exists after its first write. `~/.sakthai/` is currently absent on this
box, so each persona's first memory-writing tool call creates its own shard.

## 3. Dispatch shape

**One message containing six `Agent` calls, sent together — not one at a time.** Six
concurrent subagents is what "get all six going" means; serialising them (SakKing, wait,
SakSee, wait…) is exactly what this skill exists to prevent. No persona's dispatch is
gated on another's result, and one failure does not block reporting the other five.

## 4. Task selection

Backlog-derived per persona, in the skill's stated order — persona `SOUL.md` for the lane,
`personas/<name>/PLAN.md` where one exists (**only `saksee` and `sakjules` have one**),
then root `PLAN.md`, then recent `docs/`:

| Persona | Backlog source | Item picked |
|---|---|---|
| SakKing  | root `PLAN.md` — `[/]` in progress | Hermes profile scaffold repair, uncommitted, awaiting go-ahead |
| SakThai  | root `PLAN.md` `[/]` + `docs/hf-cards-improvement-plan.md` | HF Ecosystem Improvement, Phase 1 (broken/skeleton repos) |
| SakSee   | `personas/saksee/PLAN.md` Phases 1–2 | Browser/executable audit + CUA driver & DevTools MCP audit |
| SakSit   | `docs/hf-cards-improvement-plan.md` global rules + SOUL charge rules | Enrich thin HF cards to Rich tier, drafts held for Beer |
| SakJules | root `PLAN.md` "**Not done**" + `docs/test-coverage-audit-2026-08-27.md` | Make the 96% coverage floor actually gate CI |
| SakTan   | `SOUL.md` ops lane + `product/TODO.md` | Family daily-briefing format + today's ops surface |

---

## 5. The six Agent calls — verbatim, all in one message

### 5.1 SakKing

```
Agent(
  subagent_type="general-purpose",
  description="SakKing live auto-cycle",
  prompt="""
You are dispatching work for the sakking persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  uv run sakthai run "Work your backlog: the Hermes profile scaffold repair tracked as in-progress in root PLAN.md. Re-verify the 11 restored files under infra/hermes-agents/{default,profiles/*} against debd90de, confirm scripts/diagnose_personas.py passes 6/6 hermes-profile-scaffold checks using .venv/bin/python3 (system python3 cannot import sakthai and will give a false failure on the MCP-load subcheck), and confirm both regressed checks in diagnose_personas.py and export_agent_repo.py are sakthai-keyed rather than sakking-keyed. Leave the work staged and report exactly what a commit would contain; do not commit. Record findings to memory." \\
    --persona sakking \\
    --with-skills Sak-auto-cycle-loop \\
    --max-iterations 40 --max-seconds 1800

This is a LIVE run: no --dry-run and no SAKTHAI_HOME (the unset fallback
~/.sakthai/sakking/memory.db is the production shard and is the intended target).
Do not add --model, --provider, --no-mcp, --dry-run or SAKTHAI_HOME.

Report back: rounds completed (up to 3), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

### 5.2 SakThai

```
Agent(
  subagent_type="general-purpose",
  description="SakThai live auto-cycle",
  prompt="""
You are dispatching work for the sakthai persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  uv run sakthai run "Work your backlog as HF master: root PLAN.md marks 'HF Ecosystem Improvement' in progress with Phase 1 (broken/skeleton repo fixes) next, per docs/hf-cards-improvement-plan.md. Audit the Hub repos against that plan's global rules — no hardcoded download counts, one family table per card, story only on the profile card, honest eval labelling, canonical counts — and identify every broken or skeleton repo. Also re-check the recorded caveat that an automated promotion process re-committed the old funnel to sakthai-combined-v6, and whether it has run again. Produce the Phase 1 work order; make no Hub writes without confirming they match the plan. Record findings to memory." \\
    --persona sakthai \\
    --with-skills Sak-auto-cycle-loop \\
    --max-iterations 40 --max-seconds 1800

This is a LIVE run: no --dry-run and no SAKTHAI_HOME (the unset fallback
~/.sakthai/sakthai/memory.db is the production shard and is the intended target).
Do not add --model, --provider, --no-mcp, --dry-run or SAKTHAI_HOME.

Report back: rounds completed (up to 3), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

### 5.3 SakSee

```
Agent(
  subagent_type="general-purpose",
  description="SakSee live auto-cycle",
  prompt="""
You are dispatching work for the saksee persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  uv run sakthai run "Work your backlog from personas/saksee/PLAN.md, Phases 1 and 2 in order. Task 1.1: verify the Playwright Chromium binary at ~/.cache/ms-playwright/chromium-1155 and the Comet executable at COMET_EXE_PATH exist. Task 1.2: verify the local GGUF browser model hf.co/Nanthasit/sakthai-coder-browser-gguf is present in Ollama and that the vision API answers. Task 2.1: verify the cua-driver daemon socket. Task 2.2: audit the chrome-devtools-mcp stdio command. Every result you write must carry a retrieved_at ISO timestamp. Record findings to memory with the monitoring-result tag so no sibling has to re-check them." \\
    --persona saksee \\
    --with-skills Sak-auto-cycle-loop \\
    --max-iterations 40 --max-seconds 1800

This is a LIVE run: no --dry-run and no SAKTHAI_HOME (the unset fallback
~/.sakthai/saksee/memory.db is the production shard and is the intended target).
Do not add --model, --provider, --no-mcp, --dry-run or SAKTHAI_HOME.

Report back: rounds completed (up to 3), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

### 5.4 SakSit

```
Agent(
  subagent_type="general-purpose",
  description="SakSit live auto-cycle",
  prompt="""
You are dispatching work for the saksit persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  uv run sakthai run "Work your backlog on the content layer of the HF ecosystem push. Using the global rules in docs/hf-cards-improvement-plan.md, find the cards still sitting at Thin tier, draft the enrichment copy to bring them to Rich tier, and strip any surviving funnel sections, hardcoded download numbers, duplicated family tables, or repeated personal-story blocks that belong only on the profile card. Nothing goes public without Beer's approval and nothing about capabilities goes on the Hub without verification — write each draft to memory tagged hub-draft and awaiting-review, and hand the queue to SakThai to push. Record findings to memory." \\
    --persona saksit \\
    --with-skills Sak-auto-cycle-loop \\
    --max-iterations 40 --max-seconds 1800

This is a LIVE run: no --dry-run and no SAKTHAI_HOME (the unset fallback
~/.sakthai/saksit/memory.db is the production shard and is the intended target).
Do not add --model, --provider, --no-mcp, --dry-run or SAKTHAI_HOME.

Report back: rounds completed (up to 3), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

### 5.5 SakJules

```
Agent(
  subagent_type="general-purpose",
  description="SakJules live auto-cycle",
  prompt="""
You are dispatching work for the sakjules persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  uv run sakthai run "Work your backlog: root PLAN.md's freshness audit lists exactly one item as 'Not done' — adding --cov-fail-under=96 to ci.yml so the coverage floor actually gates the build. Per docs/test-coverage-audit-2026-08-27.md the suite sits at 95.849% locally and 95.88% in CI against fail_under = 96, and CI reports the test step as success while printing the failure line, so the floor is currently decorative. Reproduce that mechanism before diagnosing it, then close the ~0.15pp gap with real tests on the named uncovered paths (web-auth rejection branches, team/engine.py parallel failures, the SAKTHAI_* env readers) and only then wire the gate. Do not open a second PR if one already exists. Record findings to memory." \\
    --persona sakjules \\
    --with-skills Sak-auto-cycle-loop \\
    --max-iterations 40 --max-seconds 1800

This is a LIVE run: no --dry-run and no SAKTHAI_HOME (the unset fallback
~/.sakthai/sakjules/memory.db is the production shard and is the intended target).
Do not add --model, --provider, --no-mcp, --dry-run or SAKTHAI_HOME.

Report back: rounds completed (up to 3), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

### 5.6 SakTan

```
Agent(
  subagent_type="general-purpose",
  description="SakTan live auto-cycle",
  prompt="""
You are dispatching work for the saktan persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  uv run sakthai run "Work your backlog on the ops lane: the family's shared daily briefing format and today's ops surface. Read shared memory first for Beer's routines, preferences and energy levels rather than dumping a full agenda. Reconcile product/TODO.md against root PLAN.md's in-progress items and surface only what genuinely needs attention today, naming which sibling owns each. Stay in your lane — you keep the day running, you do not set technical direction, drive the web, write content or touch CI. Record the briefing and the ops rhythm to memory." \\
    --persona saktan \\
    --with-skills Sak-auto-cycle-loop \\
    --max-iterations 40 --max-seconds 1800

This is a LIVE run: no --dry-run and no SAKTHAI_HOME (the unset fallback
~/.sakthai/saktan/memory.db is the production shard and is the intended target).
Do not add --model, --provider, --no-mcp, --dry-run or SAKTHAI_HOME.

Report back: rounds completed (up to 3), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

---

## 6. Pre-flight checklist against the skill's red flags

| Red flag | Status |
|---|---|
| Dropping `--dry-run` without explicit authorization | Not applicable — authorization was explicit and quoted above |
| Dispatching persona 1, waiting, then persona 2 | Avoided — one message, six concurrent `Agent` calls |
| Passing `--provider anthropic` or an explicit `--model` | Avoided — omitted on all six; each persona's `config.yaml` decides (SakTan `ollama`, the other five `huggingface`) |
| `SAKTHAI_HOME` set to a persona's real home alongside `--persona` | Avoided — `SAKTHAI_HOME` is unset on all six |
| Mixing live and test across the six | Avoided — all six live, identical flags |
| Stopping to ask "test or live?" before a safe default | Not applicable — the user named live; dispatched without a further round-trip |
