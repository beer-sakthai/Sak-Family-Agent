# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`sakthai-agent` **v2.0** — a personal learning agent with persistent memory. It
gives a Claude or Gemini agent a durable SQLite memory it can read and write
across sessions, plus a shared tool registry and an MCP stdio server so the same
memory is reachable from other runtimes.

This is a **clean, from-scratch rewrite** of the original `SakThai-Agent` (the
"OG"). The OG is a read-only blueprint: consult it for intent, but never copy its
code or layout into this repo — re-derive everything. Notably, the OG's Google
ADK / Vertex AI cloud agent is **not** part of v2 (roadmap only), so there is **no
`app/` cloud bundle and no `sync-app-package.sh` sync step** here.

## Commands

```bash
# Setup (Python >=3.11)
cp .env.example .env            # then fill in ANTHROPIC_API_KEY
pip install -e ".[dev]"         # editable install
pip install -e ".[dashboard]"   # adds streamlit/plotly/pandas for `sakthai dashboard`
pip install -e ".[all]"         # dev + dashboard

# Test / lint / type-check / security (mirrors .github/workflows/ci.yml)
python -m pytest tests/ -q                    # full unit suite (no network, no GCP)
python -m pytest tests/test_memory_store.py -q  # a single test file
ruff check sakthai tests                      # lint
ruff format --check sakthai tests             # format check (drop --check to apply)
mypy sakthai                                  # strict type-check
bandit -c pyproject.toml -r sakthai           # security scan
```

CI runs the lint → format-check → mypy → bandit → pytest sequence on Python
**3.11 and 3.12**. Run it locally before pushing; green CI is the bar for `main`.

## Runtime entry points

One package, three ways in — all sharing `~/.sakthai/memory.db` (override the
root with `SAKTHAI_HOME`):

1. **CLI** — `sakthai <cmd>` (entry point `sakthai.cli:main`). Memory: `learn`,
   `recall`, `memory show|stats|search|export|import|backup|consolidate|deduplicate`.
   Agent: `run "<task>"`. Server: `mcp`. Plus `cycle`, `skills`, `extensions`,
   `dashboard`, `doctor`, `setup`, `tools`.
2. **Agent loop** — `sakthai run` drives a provider-agnostic tool-using loop
   (Claude or Gemini).
3. **MCP server** — `sakthai mcp` serves the same tools over JSON-RPC stdio.

## Architecture (the big picture)

A small, strictly layered package — each layer has one job. Data flows
CLI/MCP → agent loop → tool registry → MemoryStore → SQLite. See
[`docs/architecture.md`](docs/architecture.md) for the full diagram.

- **`config.py`** — the single source of truth for paths and env-var names
  (`sakthai_home`, `memory_db_path`, `sessions_dir`, `check_env`). Nothing else
  hard-codes a path; new paths go here.
- **`auth.py`** — credential resolution. Always call `resolve_anthropic_client()`
  rather than constructing a client. Anthropic chain: `ANTHROPIC_API_KEY` →
  `ANTHROPIC_AUTH_TOKEN` → Claude CLI OAuth token. Google uses the Gemini CLI
  OAuth token.
- **`memory/store.py`** — `MemoryStore` is the **only** code that touches SQLite.
  It holds *facts* and *observations* with search, tagging, dedupe,
  consolidation, stats, and snapshot import/export. Schema changes are additive
  migrations in `_migrate_schema()` (ALTER TABLE only, under `BEGIN IMMEDIATE`).
- **`agent/tools.py`** — the shared tool registry (one schema + handler per
  tool), used by **both** the agent loop and the MCP server. Add a tool once
  here and it appears in both surfaces.
- **`agent/loop.py`** — `run_agent` injects `store.render_prompt_block()` into
  the system prompt and dispatches tool calls. Client and store are injectable
  for testing. Each call writes a session log to `~/.sakthai/sessions/`.
- **`mcp/server.py`** — dependency-free JSON-RPC 2.0 stdio server.
  `handle_request` is a **pure function**, so the protocol is unit-testable with
  no process.
- **`cli/`** — click commands split by area (`agent`, `cycle`, `dashboard`,
  `extensions`, `memory`, `skills`, `system`).
- **`cycle/`** — the six-stage Dream → Hope → Care → Joy → Trust → Growth state
  machine, persisted as a single fact in the store.
- **`skills.py` + `skills/` + `library/`** — parse/catalog/validate `SKILL.md`
  files; `library/` is the curated skill set, grouped by category.
- **`dashboard/`** — `data.py` builds a testable, UI-free snapshot of the store;
  `app.py` renders it with Streamlit. `web/` is a zero-build static front-end
  reading the JSON snapshot.

## Conventions specific to this repo

- **The memory store is the seam.** Anything touching SQLite goes through
  `MemoryStore`; anything an agent or MCP client can do goes through the
  `agent/tools.py` registry. Don't bypass either.
- **Tests assume no network and no GCP credentials.** Keep them hermetic; inject
  clients/stores instead of reaching out.
- **Sandbox defaults are deliberate.** `read_file` is restricted to cwd +
  `~/.sakthai` + `SAKTHAI_READ_ALLOW`; `run_command` is **opt-in** via
  `SAKTHAI_SHELL_ALLOW`. Don't widen these without reason.
- **Not type-checked / not in CI lint:** `library/`, `scripts/`, `scratch/`,
  `web/` are excluded from ruff; `scratch/` is throwaway prototypes (not packaged).
- **mypy is `strict`** over `sakthai/` (the Streamlit `dashboard/app.py` is the
  one loosened module). Keep new code strict-clean.

## Key environment variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic auth for `sakthai run` / `mcp` (or `ANTHROPIC_AUTH_TOKEN`, or Claude CLI OAuth) |
| `SAKTHAI_HOME` | Override the `~/.sakthai` root (memory db, sessions, extensions) |
| `SAKTHAI_READ_ALLOW` | Extra paths the `read_file` tool may read |
| `SAKTHAI_SHELL_ALLOW` | Opt-in flag enabling the `run_command` tool |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Needed for the `send_telegram_message` tool |
