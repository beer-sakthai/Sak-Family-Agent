# Sak Family Auto-Cycle — Dispatch Plan

Skill: `Sak-family-auto-cycle` (snapshot at
`.claude/skill-workspaces/Sak-family-auto-cycle-workspace/skill-snapshot/SKILL.md`)
Date: 2026-08-28

---

## 1. Mode decision: **LIVE** (real homes, no `--dry-run`)

The skill's default is test mode, and the bar for overriding it is that the
user's own words unambiguously authorize a live run — the skill names
"do a live run," "this is for real, no dry-run," and "point it at the real
homes" as qualifying phrases.

The user's request was, verbatim:

> get all six personas going on their backlogs, this is for real, point them at the actual homes

That contains **two** of the skill's own example authorizations back to back —
"this is for real" and "point them at the actual homes" (= "point it at the real
homes"). This is not me reasoning that "they clearly want it to actually do
something" from a neutral phrase like "just run it"; the authorization is
explicit and in the user's own words. So: live mode.

Consequences applied consistently:

- `--dry-run` is **dropped** from all six commands.
- `SAKTHAI_HOME=$(mktemp -d)` is **replaced** by the real per-persona home from
  the skill's dispatch table.
- **No mixing** — all six are live. Not five live and one test.
- Live means real API spend across six concurrent agents and real writes to
  persona memory. That is what was asked for.

Everything else stays as the skill specifies: `--with-skills Sak-auto-cycle-loop`,
`--provider anthropic`, `--max-iterations 40`, `--max-seconds 1800`, up to 3
Dream→Hope→Care→Joy→Trust→Growth rounds per persona.

## 2. Dispatch shape: **one message, six Agent calls**

All six Agent tool calls below go out **in a single message**, dispatched
together, running concurrently. Not one at a time. Not "SakKing first, check the
result, then SakThai." The parallel fan-out is the point of the skill — six
subagents in flight at once is what "get all six personas going" means. I collect
all six results and only then write the consolidated report.

## 3. Homes and memory database paths

`config.memory_db_path()` is `sakthai_home() / "memory.db"`, and
`sakthai_home()` returns `$SAKTHAI_HOME` when set
(`personas/sakthai/sakthai/config.py:146-187`). So each run reads and writes
exactly one database, resolved from the `SAKTHAI_HOME` on its command line:

| Persona | `SAKTHAI_HOME` (live) | Memory DB read+written |
|---|---|---|
| SakKing | `/opt/data` | `/opt/data/memory.db` |
| SakThai | `/opt/data/profiles/sakthai` | `/opt/data/profiles/sakthai/memory.db` |
| SakSee | `/opt/data/profiles/saksee` | `/opt/data/profiles/saksee/memory.db` |
| SakSit | `/opt/data/profiles/saksit` | `/opt/data/profiles/saksit/memory.db` |
| SakTan | `/opt/data/profiles/saktan` | `/opt/data/profiles/saktan/memory.db` |
| SakJules | `/opt/data/profiles/sakjules` | `/opt/data/profiles/sakjules/memory.db` |

Note the asymmetry, which is easy to get wrong: **SakKing's home is `/opt/data`
directly — there is no `/opt/data/profiles/sakking`.** The other five each sit
under `/opt/data/profiles/<lowercase-name>`.

Sessions and the eval log follow the same root, so each persona's run also writes
`$SAKTHAI_HOME/sessions/` and `$SAKTHAI_HOME/eval.jsonl` under its own home.

## 4. Where each persona's task came from

The user said "their backlogs" without enumerating six tasks, so per the skill I
sourced each task from that persona's own backlog docs rather than stopping to
ask:

| Persona | Source |
|---|---|
| SakKing | root `PLAN.md` line 63 — Hermes profile scaffold repair, `[/]` in progress, uncommitted |
| SakThai | root `PLAN.md` line 62 + `docs/hf-cards-improvement-plan.md` — HF ecosystem plan, `[/]` awaiting Phase 1 start |
| SakSee | `personas/saksee/PLAN.md` Phases 1–2 (browser/CUA/DevTools audit) |
| SakSit | `docs/hf-cards-improvement-plan.md` card-copy counts (19/16/7) + `dataset-cards/`; SakSit owns Hub content per `personas/saksit/SOUL.md` |
| SakTan | `personas/saktan/SOUL.md` "concrete surface" — daily schedule templates, ops workflows, shared briefing format; cron inventory (cron confirmed dead in the HF plan) |
| SakJules | `personas/sakjules/PLAN.md` Phases 1–2 (credential audit, daemon health, OpenCode model matrix) + `apps.yml` generated-types drift |

---

## 5. The six Agent tool calls — verbatim, sent together in one message

### Call 1 — SakKing

```
Agent(
  subagent_type: "general-purpose",
  description: "SakKing auto-cycle round",
  prompt: """
You are dispatching work for the SakKing persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=/opt/data uv run sakthai run "Finish the Hermes profile scaffold repair: re-run scripts/diagnose_personas.py with .venv/bin/python3 and confirm 6/6 hermes-profile-scaffold checks pass across all six agents, verify the 11 files restored from debd90de are intact and both the diagnose_personas.py and export_agent_repo.py default-profile checks are sakthai-keyed, then write up exactly what remains before Beer can commit" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800

Report back: how many cycle rounds completed, the task and outcome of each
round, any lessons learned, and any blockers or failures.
"""
)
```

### Call 2 — SakThai

```
Agent(
  subagent_type: "general-purpose",
  description: "SakThai auto-cycle round",
  prompt: """
You are dispatching work for the SakThai persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=/opt/data/profiles/sakthai uv run sakthai run "Start Phase 1 of the HF ecosystem improvement plan in docs/hf-cards-improvement-plan.md: identify the broken and skeleton Hub repos across Beer's 23 models / 15 datasets / 6 Spaces, classify each as fix-now, needs-content, or archive, and produce the Phase 1 worklist with the card and metadata gaps named per repo" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800

Report back: how many cycle rounds completed, the task and outcome of each
round, any lessons learned, and any blockers or failures.
"""
)
```

### Call 3 — SakSee

```
Agent(
  subagent_type: "general-purpose",
  description: "SakSee auto-cycle round",
  prompt: """
You are dispatching work for the SakSee persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=/opt/data/profiles/saksee uv run sakthai run "Work Phases 1 and 2 of personas/saksee/PLAN.md: audit the Playwright Chromium and Comet executables, health-check the local GGUF browser model and the vision API, verify the cua-driver socket and the chrome-devtools-mcp stdio discovery, and record pass/fail plus the exact blocker for every acceptance criterion that does not hold" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800

Report back: how many cycle rounds completed, the task and outcome of each
round, any lessons learned, and any blockers or failures.
"""
)
```

### Call 4 — SakSit

```
Agent(
  subagent_type: "general-purpose",
  description: "SakSit auto-cycle round",
  prompt: """
You are dispatching work for the SakSit persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=/opt/data/profiles/saksit uv run sakthai run "Own the content half of the HF cards improvement plan: draft the card and metadata copy for the model, dataset and Space repos flagged in docs/hf-cards-improvement-plan.md, keeping every capability claim traceable to something verified rather than asserted, and stage the drafts for Beer's approval without publishing anything" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800

Report back: how many cycle rounds completed, the task and outcome of each
round, any lessons learned, and any blockers or failures.
"""
)
```

### Call 5 — SakTan

```
Agent(
  subagent_type: "general-purpose",
  description: "SakTan auto-cycle round",
  prompt: """
You are dispatching work for the SakTan persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=/opt/data/profiles/saktan uv run sakthai run "Rebuild the family's recurring-ops picture: inventory every scheduled and recurring task the household depends on, confirm which cron jobs are actually dead versus assumed live, refresh the daily schedule templates and the shared daily briefing format under personas/saktan/skills/, and write the cron specifications SakJules would need to re-implement the dead ones" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800

Report back: how many cycle rounds completed, the task and outcome of each
round, any lessons learned, and any blockers or failures.
"""
)
```

### Call 6 — SakJules

```
Agent(
  subagent_type: "general-purpose",
  description: "SakJules auto-cycle round",
  prompt: """
You are dispatching work for the SakJules persona of the Sak Family agent.
Run:

  SAKTHAI_HOME=/opt/data/profiles/sakjules uv run sakthai run "Work Phases 1 and 2 of personas/sakjules/PLAN.md: audit that the five required API credentials resolve, health-check the local Supermemory daemon on port 6767, verify opencode.json is 100% custom Nanthasit models with zero Gemini quota dependency, then check apps.yml for generated-TypeScript drift against web/contracts.py and report any red gate with the failing job named" \
    --with-skills Sak-auto-cycle-loop \
    --provider anthropic --max-iterations 40 --max-seconds 1800

Report back: how many cycle rounds completed, the task and outcome of each
round, any lessons learned, and any blockers or failures.
"""
)
```

---

## 6. Dispatch note

**Single message, six calls, concurrent.** Calls 1–6 above are issued together in
one assistant message. No persona's result is inspected before another is
launched; results are gathered as all six return, and the consolidated report
(`report.md`) is written only after the last one lands. A persona that fails
still gets a row — one failure does not hold up reporting the other five.
