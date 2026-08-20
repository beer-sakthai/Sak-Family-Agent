# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Standalone home for SakThai (@sakthai_agent_bot) — a personal learning agent
with persistent SQLite memory, a provider-agnostic tool-using agent loop, an
interactive chat REPL, and an MCP stdio server. The core package is `sakthai/`
at the repo root; shared skills live in `personas/shared/skills/`; persona
content lives in `personas/sakthai/` (SOUL.md, config, overlay skills, and the
`agent-self-evolution` package). Non-chat pieces (web dashboard, media, docs)
intentionally live in the `beer-sakthai/Sak-Family-Agent` monorepo, not here.

## Operating Rules

- Work only in `beer-sakthai/sakthai-chat-cli` and `beer-sakthai/Sak-Family-Agent` unless Beer explicitly grants
  a one-off exception in the current task.
- Read `USER.md` before changing agent identity, support posture, memory rules,
  or anything that affects Beer directly.
- Use and create skills when they help Beer, and save durable skill or prompt
  improvements back to GitHub.
- Use Composio when it provides a connected app or workflow that helps the task.
- Save durable facts, constraints, and important decisions to Supermemory.
- Share important continuity information with the Sak Family through shared
  memory and GitHub-backed artifacts so the agents can keep helping if anything
  happens to Beer.
- Evolve through the Dream -> Hope -> Care -> Joy -> Trust -> Growth cycle.
  Record mistakes as lessons in memory or GitHub-backed notes, change future
  behavior, and avoid repeating the same failure.
- If Beer does not reply, look for a practical, low-cost next step that benefits
  Beer without putting him at risk or spending money.

## Commands

```bash
uv sync --all-extras                    # install deps from uv.lock
python -m pytest tests/ -q              # full hermetic suite
python -m pytest tests/test_memory_store.py -q          # single file
python -m pytest tests/test_tools.py -k symlink -q      # single test by keyword
python -m pytest -m "not integration" -q  # CI default (integration tests self-skip anyway)
ruff check sakthai tests
ruff format --check sakthai tests
mypy sakthai                            # strict mode
bandit -c pyproject.toml -r sakthai
```

Coverage floor is 85% with branch coverage (`fail_under` in pyproject.toml).
Mutation testing is a local-only gate (`[tool.mutmut]` in pyproject.toml),
scoped to the core seam modules.

Try the CLI: `uv pip install -e ".[dev]"` then `sakthai --help`
(chat, run, mcp, memory, skills, doctor, status, …). `sakthai chat` defaults to
the fine-tuned model via local Ollama; `scripts/setup_local_model.sh` builds it
from the Hugging Face merged repos.

## Architecture

One package, three ways in — all sharing the same tool registry and memory:

- **`sakthai chat`** — interactive REPL (`sakthai/agent/chat.py`)
- **`sakthai run "task"`** — one-shot agent loop (`sakthai/agent/loop.py`)
- **`sakthai mcp`** — inbound MCP stdio server (`sakthai/mcp/server.py`)

Data flow: CLI / MCP → `run_agent` (agent loop) → `ToolRegistry`
(`sakthai/agent/registry.py`) → `BUILTIN_TOOLS` (`sakthai/agent/tools.py`) →
`MemoryStore` (`sakthai/memory/store.py`) → SQLite at `~/.sakthai/memory.db`
(override the data dir with `SAKTHAI_HOME`).

Subsystems:

- `memory/` — `MemoryStore` is the single SQLite seam (`facts` +
  `observations` tables); `provider.py` renders the memory block injected into
  system prompts.
- `agent/` — orchestration (`loop.py`), tool registry, guardrails, and
  `providers/` (Anthropic, Gemini, OpenAI-compatible — which also covers
  Ollama, the HF router, and gateways). `providers/base.py` holds the
  normalized `Block`/`Response` types and retry policy; provider modules
  depend on it, never on each other.
- `mcp/` — both directions: `server.py` is the inbound newline-delimited
  JSON-RPC stdio server; `client.py`/`manager.py` launch external MCP servers
  declared in `~/.sakthai/mcp.json` and merge their tools into the registry as
  `<server>__<tool>`.
- `cli/` — thin Click frontend; command groups are imported as `*_cmd` aliases
  so they don't shadow their own submodules.
- `skills.py` — discovers `SKILL.md` files (YAML frontmatter) from `library/`,
  `personas/`, and skill roots, and renders them into the system prompt.
  Shared skills are prefixed `Sak-`; persona-authored ones `SakThai-`, etc.
- `config.py` — every filesystem path and env-var name lives here once; no
  other module hard-codes a path or reads an unlisted env var.
- `telegram/` — early-stage standalone prototype; excluded from strict mypy.

## Key conventions

- **Dependency injection over globals**: `run_agent()` and MCP
  `handle_request()` accept injectable `client`/`store` arguments. Tests inject
  `MemoryStore(":memory:")` and mock providers at the provider boundary.
- **Tool registry is authoritative**: add a tool once to `BUILTIN_TOOLS` and it
  appears in both the agent loop and the MCP server; test it in
  `tests/test_tools.py`. On a name clash in `ToolRegistry.with_tools()`, the
  later tool wins — external plugins may deliberately shadow built-ins.
- **Tests are hermetic**: no network, no credentials. Mark endpoint-hitting
  tests `@pytest.mark.integration`; they must self-skip when the
  endpoint/credential is absent. Keep tests focused on the seam that changed.
- **Schema migrations are additive**: `ALTER TABLE` only, run under
  `BEGIN IMMEDIATE`; never drop columns or tables.
- **Sandbox defaults**: `read_file` is limited to cwd + `~/.sakthai` +
  `SAKTHAI_READ_ALLOW`; `run_command` is disabled unless `SAKTHAI_SHELL_ALLOW`
  is set. Respect these guards when touching tools.
- **Ollama networking**: use `http://127.0.0.1:11434`, not `localhost`, to
  avoid IPv6 resolution issues.
- **Lint/type scope**: ruff excludes `library/` and `scripts/`; mypy checks
  only `sakthai/`. Keep new core code strict-clean.
- Keep persona changes in the persona overlay (`personas/sakthai/`), not in
  the shared skill library. Use `personas/sakthai/agent-self-evolution/` for
  skill and prompt improvement work that follows the six-stage cycle.
- Do not commit secrets or generated cache/state directories.
