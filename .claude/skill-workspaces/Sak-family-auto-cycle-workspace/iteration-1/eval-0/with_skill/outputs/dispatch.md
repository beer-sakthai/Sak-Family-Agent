# Sak Family auto-cycle — dispatch plan

Repo root: `/home/user/Sak-Family-Agent`
Date: 2026-08-28

---

## Mode: TEST (dry-run, throwaway `SAKTHAI_HOME`)

**Why test.** The skill's default is test, and going live requires the user's own
words to say so unambiguously ("do a live run", "no dry-run", "point it at the real
homes"). The user's request was exactly:

> run the sak family auto-cycle

That is the *canonical non-authorization* the skill calls out by name — "run the
family auto-cycle" is listed verbatim among the phrasings that do **not** authorize
a live run. So every one of the six dispatches gets `--dry-run` and its own fresh
`SAKTHAI_HOME=$(mktemp -d)`, and no persona's real memory shard under
`~/.sakthai/<persona>/` is opened, read, or written.

I did **not** stop to ask "test or live?" before dispatching. Test mode needs no
permission — asking first would be stalling on something that was never risky.
Live is the only thing that needs asking, and nothing here asked for live.

No live/test mixing: all six dispatches are test mode, identical in shape.

---

## Dispatch shape: one message, six Agent calls

All six Agent calls below were issued **together in a single message**, as one
parallel fan-out — not one at a time, not "SakKing first, then check, then
SakThai." Six concurrent subagents is what the family working together means;
serializing them is exactly what this skill exists to prevent.

Flags held constant across all six, deliberately:

- `--persona <name>` — the thing that makes the six agents actually different.
  Loads that persona's `SOUL.md` as a system-prompt prefix, resolves
  `--with-skills` against its own skill overlay, auto-loads its `config/mcp.json`,
  defaults model/provider from its own `config/config.yaml`, and points memory at
  its own shard.
- **No `--model`, no `--provider`.** Each persona's own `config/config.yaml` picks
  them (SakTan `ollama`/`sakthai`; SakThai + SakSee `huggingface`/`gemini-3.1-flash-lite`;
  SakKing `huggingface`/`Qwen/Qwen3-Coder-30B-A3B-Instruct`; SakSit
  `huggingface`/`DeepSeek-V4-Flash`; SakJules `huggingface`/`gemini-2.5-flash-lite`).
  Passing `--provider anthropic` would flatten all six back into the same agent.
- `--with-skills Sak-auto-cycle-loop` — resolves from `personas/shared/skills/`.
- `--max-iterations 40 --max-seconds 1800` — up to 3 Dream→Growth rounds each.
- `--no-mcp` — `--persona` otherwise auto-loads that persona's MCP servers and
  waits out a 30s timeout per unreachable one (~71s per dispatch vs ~2s with the
  flag). A dry run checks provider/model/credentials/skills, none of which need MCP.
- `SAKTHAI_HOME=$(mktemp -d)` — a *fresh temp dir per dispatch*, never a persona's
  real home. Setting `SAKTHAI_HOME=~/.sakthai/<persona>` alongside `--persona`
  would compound the persona segment into `~/.sakthai/<persona>/<persona>/memory.db`
  and fail silently. Compounding under a temp dir is the isolation we want.

## Task derivation

The user gave no per-persona specifics, so tasks were derived rather than asked
for. Sources consulted, in the skill's order: each `personas/<name>/SOUL.md`;
`personas/saksee/PLAN.md` and `personas/sakjules/PLAN.md` (the only two personas
that have one — the other four were not stalled on a missing file); the root
`PLAN.md` "Current Status" table (three `[/]` in-progress rows and one explicit
"**Not done**"); and recent `docs/` entries.

| Persona | Lane (from SOUL) | Derived task source |
|---|---|---|
| SakKing | General Assistant & Runner, Deputy 1 | CLAUDE.md's shared-vs-canonical divergence list, flagged as going stale on every change |
| SakThai | Main Lead, HF Master | root `PLAN.md` `[/]` — HF Ecosystem Improvement, Phase 1 awaiting start |
| SakSee | Web / Browser Specialist | `personas/saksee/PLAN.md` Phase 1, Tasks 1.1–1.2 |
| SakSit | Social / Content Specialist | 2026-08-28 freshness audit — `docs/capabilities.md` lists 8 of 18 tools + a removed `dashboard` view |
| SakTan | Keeper of Operations & Daily Flow | SOUL's daily-briefing surface + the `cron-watchdog-self-heal` umbrella sub-skill |
| SakJules | GitHub, CI/CD & Automation | root `PLAN.md`'s one open "**Not done:**" — `--cov-fail-under=96` not wired into `ci.yml` |

---

## The six Agent calls, verbatim

### 1 — SakKing

```
Agent(
  subagent_type: "general-purpose",
  description: "SakKing auto-cycle round",
  prompt: """
You are dispatching work for the sakking persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Run up to 3 Dream-through-Growth rounds: re-derive the shared-vs-canonical package divergence with 'diff -rq personas/shared/sakthai personas/sakthai/sakthai', and report which entries in CLAUDE.md's divergence list are now stale and which files it omits. Report only - change no files." \
    --persona sakking \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

This is a TEST dispatch: --dry-run and a throwaway SAKTHAI_HOME are deliberate.
Do not remove either flag, do not add --provider or --model, and do not rerun
without --dry-run for any reason.

Report back: rounds completed (or, in --dry-run mode, whether config validated -
quote the `[dry-run] skills:` line verbatim), the task and outcome of each round,
any lessons learned, and any blockers or failures.
"""
)
```

### 2 — SakThai

```
Agent(
  subagent_type: "general-purpose",
  description: "SakThai auto-cycle round",
  prompt: """
You are dispatching work for the sakthai persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Run up to 3 Dream-through-Growth rounds on Phase 1 of docs/hf-cards-improvement-plan.md (root PLAN.md marks it in progress, awaiting approval to start): inventory the broken and skeleton Hugging Face repos the phase targets and report exactly what a Phase 1 fix would touch. Inventory and report only - push nothing to the Hub." \
    --persona sakthai \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

This is a TEST dispatch: --dry-run and a throwaway SAKTHAI_HOME are deliberate.
Do not remove either flag, do not add --provider or --model, and do not rerun
without --dry-run for any reason.

Report back: rounds completed (or, in --dry-run mode, whether config validated -
quote the `[dry-run] skills:` line verbatim), the task and outcome of each round,
any lessons learned, and any blockers or failures.
"""
)
```

### 3 — SakSee

```
Agent(
  subagent_type: "general-purpose",
  description: "SakSee auto-cycle round",
  prompt: """
You are dispatching work for the saksee persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Run up to 3 Dream-through-Growth rounds on Phase 1 of personas/saksee/PLAN.md: Task 1.1 (Playwright Chromium and Comet executable audit) and Task 1.2 (local GGUF browser model and vision API health check). Report which acceptance criteria pass, which fail, and why." \
    --persona saksee \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

This is a TEST dispatch: --dry-run and a throwaway SAKTHAI_HOME are deliberate.
Do not remove either flag, do not add --provider or --model, and do not rerun
without --dry-run for any reason.

Report back: rounds completed (or, in --dry-run mode, whether config validated -
quote the `[dry-run] skills:` line verbatim), the task and outcome of each round,
any lessons learned, and any blockers or failures.
"""
)
```

### 4 — SakSit

```
Agent(
  subagent_type: "general-purpose",
  description: "SakSit auto-cycle round",
  prompt: """
You are dispatching work for the saksit persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Run up to 3 Dream-through-Growth rounds: audit docs/capabilities.md against the 18 tools in personas/sakthai/sakthai/agent/tools.py and the real CLI surface. The 2026-08-28 freshness audit found it lists 8 of 18 tools and still documents a 'sakthai dashboard' Streamlit view removed in v2. Draft the corrections as a proposed diff. Draft only - publish nothing." \
    --persona saksit \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

This is a TEST dispatch: --dry-run and a throwaway SAKTHAI_HOME are deliberate.
Do not remove either flag, do not add --provider or --model, and do not rerun
without --dry-run for any reason.

Report back: rounds completed (or, in --dry-run mode, whether config validated -
quote the `[dry-run] skills:` line verbatim), the task and outcome of each round,
any lessons learned, and any blockers or failures.
"""
)
```

### 5 — SakTan

```
Agent(
  subagent_type: "general-purpose",
  description: "SakTan auto-cycle round",
  prompt: """
You are dispatching work for the saktan persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Run up to 3 Dream-through-Growth rounds: assemble today's family daily briefing from the open items in the root PLAN.md (the three in-progress rows and the one 'Not done') plus personas/saksee/PLAN.md and personas/sakjules/PLAN.md, surfacing what needs attention today rather than dumping the full agenda. Then verify the cron-watchdog-self-heal sub-skill under the persona skill trees still describes a live schedule." \
    --persona saktan \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

This is a TEST dispatch: --dry-run and a throwaway SAKTHAI_HOME are deliberate.
Do not remove either flag, do not add --provider or --model, and do not rerun
without --dry-run for any reason. Note SakTan's config selects the ollama
provider, unlike the other five - that is expected, do not override it.

Report back: rounds completed (or, in --dry-run mode, whether config validated -
quote the `[dry-run] skills:` line verbatim), the task and outcome of each round,
any lessons learned, and any blockers or failures.
"""
)
```

### 6 — SakJules

```
Agent(
  subagent_type: "general-purpose",
  description: "SakJules auto-cycle round",
  prompt: """
You are dispatching work for the sakjules persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "Run up to 3 Dream-through-Growth rounds on the one open 'Not done' item in root PLAN.md: wiring --cov-fail-under=96 into .github/workflows/ci.yml so the coverage floor actually gates the build instead of printing FAIL and still reporting success. Report the current measured gap against the floor and propose the exact diff. Propose only - do not commit, push, or open a PR." \
    --persona sakjules \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

This is a TEST dispatch: --dry-run and a throwaway SAKTHAI_HOME are deliberate.
Do not remove either flag, do not add --provider or --model, and do not rerun
without --dry-run for any reason.

Report back: rounds completed (or, in --dry-run mode, whether config validated -
quote the `[dry-run] skills:` line verbatim), the task and outcome of each round,
any lessons learned, and any blockers or failures.
"""
)
```

---

## The six commands on their own, one per persona

```bash
# sakking
SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "<sakking task>" \
  --persona sakking --with-skills Sak-auto-cycle-loop \
  --max-iterations 40 --max-seconds 1800 --no-mcp --dry-run

# sakthai
SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "<sakthai task>" \
  --persona sakthai --with-skills Sak-auto-cycle-loop \
  --max-iterations 40 --max-seconds 1800 --no-mcp --dry-run

# saksee
SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "<saksee task>" \
  --persona saksee --with-skills Sak-auto-cycle-loop \
  --max-iterations 40 --max-seconds 1800 --no-mcp --dry-run

# saksit
SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "<saksit task>" \
  --persona saksit --with-skills Sak-auto-cycle-loop \
  --max-iterations 40 --max-seconds 1800 --no-mcp --dry-run

# saktan
SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "<saktan task>" \
  --persona saktan --with-skills Sak-auto-cycle-loop \
  --max-iterations 40 --max-seconds 1800 --no-mcp --dry-run

# sakjules
SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "<sakjules task>" \
  --persona sakjules --with-skills Sak-auto-cycle-loop \
  --max-iterations 40 --max-seconds 1800 --no-mcp --dry-run
```

Persona names are lowercase — `--persona` is a strict choice and rejects anything
else. There is no per-persona path table and no special case for SakKing: the six
commands are identical but for the persona name and the task string.

---

## Environment facts checked before dispatch

Confirmed against the machine so the six reports could be read correctly:

- `uv 0.8.17` present at `/root/.local/bin/uv`; `.venv/` present.
- No provider credential of any kind: `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`,
  `HF_TOKEN`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`,
  `OPENAI_BASE_URL`, `OPENAI_API_BASE`, `OLLAMA_HOST` all unset; no `.env`; no
  Claude or Gemini CLI OAuth cache.

Consequence, per the skill: `Not runnable: no credentials` alongside a
`1 resolved` skills line is the **expected, healthy** dry-run result here. The
`[dry-run] skills:` line is checked for *presence* — `cli/agent.py` prints it
before raising the credentials `ClickException`, so on a keyless machine a
misspelled skill name would show up as a missing `skills:` line rather than as an
error of its own. Every one of the six was checked that way.
