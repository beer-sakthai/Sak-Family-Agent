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
   (Claude, Gemini, or any OpenAI-compatible/Ollama endpoint).
3. **MCP server** — `sakthai mcp` serves the same tools over JSON-RPC stdio.

`sakthai run` can also reach *out* to external MCP servers: tools discovered from
them are merged into the registry (namespaced `<server>__<tool>`) for that run.

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
  OAuth token. OpenAI/Ollama uses `resolve_openai_credentials` to locate the base URL and API key.
- **`memory/store.py`** — `MemoryStore` is the **only** code that touches SQLite.
  It holds *facts* and *observations* with search, tagging, dedupe,
  consolidation, stats, and snapshot import/export. Schema changes are additive
  migrations in `_migrate_schema()` (ALTER TABLE only, under `BEGIN IMMEDIATE`).
- **`agent/tools.py` + `agent/registry.py`** — `tools.py` defines `BUILTIN_TOOLS`
  (one schema + handler per tool); `registry.py`'s `ToolRegistry` keys tools by
  name for both the agent loop and the MCP server, and merges runtime-discovered
  tools (later tool wins on a name clash, so a plugin can shadow a built-in). Add
  a tool once in `tools.py` and it appears in both surfaces.
- **`agent/loop.py`** — `run_agent` injects `store.render_prompt_block()` into
  the system prompt and dispatches tool calls. Client and store are injectable
  for testing. Each call writes a session log to `~/.sakthai/sessions/`.
- **`mcp/server.py`** — dependency-free JSON-RPC 2.0 stdio server (inbound).
  `handle_request` is a **pure function**, so the protocol is unit-testable with
  no process.
- **`mcp/{client,manager,servers}.py`** — the outbound mirror: `servers.py`
  discovers external server specs (`~/.sakthai/mcp.json` + extensions), `client.py`
  speaks JSON-RPC to one subprocess and wraps each remote tool as a local `Tool`,
  and `manager.connect_servers()` is the context manager that starts them all
  (failing soft), yields their merged tools, and tears them down.
- **`cli/`** — click commands split by area (`agent`, `cycle`, `dashboard`,
  `extensions`, `memory`, `skills`, `system`).
- **`cycle/`** — the six-stage Dream → Hope → Care → Joy → Trust → Growth state
  machine, persisted as a single fact in the store.
- **`skills.py` + `skills/` + `library/`** — parse/catalog/validate `SKILL.md`
  files; `library/` is the curated skill set, grouped by category.
- **`dashboard/`** — `data.py` builds a testable, UI-free snapshot of the store;
  `app.py` renders it with Streamlit.

## Conventions specific to this repo

- **The memory store is the seam.** Anything touching SQLite goes through
  `MemoryStore`; anything an agent or MCP client can do goes through the
  `agent/tools.py` registry. Don't bypass either.
- **Tests assume no network and no GCP credentials.** Keep them hermetic; inject
  clients/stores instead of reaching out.
- **Sandbox defaults are deliberate.** `read_file` is restricted to cwd +
  `~/.sakthai` + `SAKTHAI_READ_ALLOW`; `run_command` is **opt-in** via
  `SAKTHAI_SHELL_ALLOW`. Don't widen these without reason.
- **Not linted / not type-checked:** ruff excludes `library/` and `scripts/`;
  mypy only covers `sakthai/`. Don't "fix" lint/types in those trees.
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
| `OLLAMA_HOST` | Local Ollama server address (defaults to `http://localhost:11434`) |
| `OPENAI_API_BASE` / `OPENAI_BASE_URL` | Base URL endpoint for OpenAI-compatible services |
| `OPENAI_API_KEY` | API key required by the OpenAI-compatible gateway (defaults to `nokey`) |
