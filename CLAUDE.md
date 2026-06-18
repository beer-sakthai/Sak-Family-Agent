# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`sakthai-agent` **v2.0** — a personal learning agent with persistent memory. It
gives a Claude or Gemini agent a durable SQLite memory it can read and write
across sessions, plus a shared tool registry and an MCP stdio server so the same
memory is reachable from other runtimes.

This is a **clean, from-scratch rewrite** of the original `SakThai-Agent` (the
"OG"). The OG is a read-only blueprint: consult it for intent, but never copy its
code or layout into this repo — re-derive everything. The OG's full Google
ADK / Vertex AI cloud agent is **not** shipped in v2: there is **no `app/` cloud
bundle and no `sync-app-package.sh` sync step** here. v2 carries only a lazy
**cloud-runtime skeleton** in `sakthai/cloud/` (the `cloud` extra; `sakthai
cloud` commands) that describes/scaffolds a deployment without importing
`google-adk` at module load — see [`docs/cloud.md`](docs/cloud.md). Actual
deployment execution remains on the roadmap.

---

## Commands

```bash
# Setup (Python >=3.11)
cp .env.example .env            # then fill in ANTHROPIC_API_KEY
pip install -e ".[dev]"         # editable install + test/lint/type-check tools
pip install -e ".[dashboard]"   # adds streamlit/plotly/pandas/PyGithub for `sakthai dashboard`
pip install -e ".[cloud]"       # adds google-adk/aiplatform/logging for `sakthai cloud`
pip install -e ".[all]"         # dev + dashboard + cloud

# Preferred: use uv (CI uses uv with uv.lock for reproducible installs)
uv sync --all-extras

# Test / lint / type-check / security (mirrors .github/workflows/ci.yml)
python -m pytest tests/ -q                      # full unit suite (no network, no GCP)
python -m pytest tests/test_memory_store.py -q  # a single test file
python -m pytest -m "not integration" -q        # exclude network tests (default in CI)
ruff check sakthai tests                        # lint
ruff format --check sakthai tests               # format check (drop --check to apply)
mypy sakthai                                    # strict type-check
bandit -c pyproject.toml -r sakthai             # security scan
```

CI runs the lint → format-check → mypy → bandit → pytest sequence on Python
**3.11, 3.12, and 3.13**. Run it locally before pushing; green CI is the bar for `main`.
CI runs secret-scan → lint → format-check → mypy → bandit → pytest on Python
**3.11 and 3.12** via uv. Run it locally before pushing; green CI is the bar for
`main`. Coverage floor is **85%** (`fail_under = 85`); `dashboard/app.py` is
excluded from coverage (it's presentation glue).

---

## Runtime entry points

One package, three ways in — all sharing `~/.sakthai/memory.db` (override the
root with `SAKTHAI_HOME`):

1. **CLI** — `sakthai <cmd>` (entry point `sakthai.cli:main`). Commands:
   - Memory: `learn`, `recall`, `memory show|stats|search|export|import|backup|consolidate|consolidate-sessions|deduplicate`
   - Agent: `run "<task>"` (with `--model`, `--max-tokens`, `--max-iterations`, `--verbose`, `--no-mcp`)
   - Server: `mcp` (start MCP stdio server)
   - Cycle: `cycle status|next|set|list`
   - Skills: `skills list|show|validate`
   - Extensions: `extensions add|list|remove`
   - Sessions: `sessions list|show|export`
   - System: `doctor`, `setup`, `status`, `tools`
   - Dashboard: `dashboard` (Streamlit UI)
   - Cloud: `cloud status|deploy|validate`

2. **Agent loop** — `sakthai run` drives a provider-agnostic tool-using loop
   (Claude, Gemini, or any OpenAI-compatible/Ollama endpoint).

3. **MCP server** — `sakthai mcp` serves the same tools over JSON-RPC stdio.

`sakthai run` can also reach *out* to external MCP servers: tools discovered from
them are merged into the registry (namespaced `<server>__<tool>`) for that run.

---

## Architecture (the big picture)

A small, strictly layered package — each layer has one job. Data flows
CLI/MCP → agent loop → tool registry → MemoryStore → SQLite. See
[`docs/architecture.md`](docs/architecture.md) for the full diagram.

### Core modules

- **`config.py`** — single source of truth for paths and env-var names
  (`sakthai_home`, `memory_db_path`, `sessions_dir`, `check_env`). Nothing else
  hard-codes a path; new paths go here.
- **`auth.py`** — credential resolution. Always call `resolve_anthropic_client()`
  rather than constructing a client. Anthropic chain: `ANTHROPIC_API_KEY` →
  `ANTHROPIC_AUTH_TOKEN` → Claude CLI OAuth token. Google uses the Gemini CLI
  OAuth token. OpenAI/Ollama uses `resolve_openai_credentials` to locate the base
  URL and API key. Raises `AuthError` when no credentials are found.

### Memory subsystem (`memory/`)

- **`memory/store.py`** — `MemoryStore` is the **only** code that touches SQLite.
  It holds *facts* (`Fact` dataclass: id, kind, key, value, source_session,
  created_at, updated_at, tags) and *observations* (`Observation` dataclass: id,
  summary, evidence_session_id, weight, confidence, created_at). Features:
  WAL concurrency, additive migrations in `_migrate_schema()` (ALTER TABLE only,
  under `BEGIN IMMEDIATE`), snapshot export/import (JSONL/CSV), deduplicate, and
  consolidate. `render_prompt_block()` injects memory into the system prompt.
- **`memory/provider.py`** — `SakThaiMemoryProvider` adapts the store to
  system-prompt blocks with context-window limiting.
- **`memory/backup.py`** — timestamped copy of `memory.db`.
- **`memory/sync.py`** — git-based JSONL export/import (multi-agent sync) and
  HTTP backup to a configured endpoint.

### Agent subsystem (`agent/`)

- **`agent/tools.py`** — defines `BUILTIN_TOOLS` (10 tools, one schema + handler
  each): `learn`, `recall`, `search`, `forget`, `list_facts`, `read_file`,
  `run_command`, `send_telegram_message`, `healthcheck`, `render_memory`. Add a
  tool here and it appears in both the agent loop and the MCP server automatically.
- **`agent/registry.py`** — `ToolRegistry` keys tools by name; `with_tools()`
  merges sets (later tool wins on name clash, so plugins can shadow built-ins).
- **`agent/loop.py`** — `run_agent()` is the main orchestration loop. Injects
  `store.render_prompt_block()` into the system prompt, dispatches tool calls,
  writes session logs to `~/.sakthai/sessions/`. Returns `AgentResult` (iterations,
  stop_reason, tool_calls, usage). Client and store are injectable for testing.
- **`agent/usage.py`** — `UsageTracker` / `extract_usage()` for token counting.
- **`agent/providers/`** — provider abstraction:
  - `base.py` — shared types (`Block`, `Response`), retry logic via `tenacity`
  - `anthropic_provider.py` — Claude via `anthropic` SDK
  - `gemini_provider.py` — Gemini via `google-genai`
  - `openai_provider.py` — OpenAI-compatible APIs and Ollama via `httpx`
  - `__init__.py` — provider detection and client factory

### MCP subsystem (`mcp/`)

- **`mcp/server.py`** — **inbound** JSON-RPC 2.0 stdio server. `handle_request`
  is a **pure function**, testable without a process. Reuses `BUILTIN_TOOLS` so
  behavior matches the agent loop exactly. Advertises protocol version
  `"2024-11-05"`.
- **`mcp/client.py`** — **outbound** stdio client. Launches external MCP servers,
  wraps their tools as local `Tool` objects, auto-namespaces as `<server>__<tool>`.
  Dependency-free; uses `select`-based timeouts (no asyncio).
- **`mcp/manager.py`** — `connect_servers()` context manager starts all configured
  servers, fails soft on errors, merges tools, cleans up on exit.
- **`mcp/servers.py`** — `MCPServerSpec` dataclass + `load_server_specs()`:
  discovers external server specs from `~/.sakthai/mcp.json` and extensions.

External MCP server config format (`~/.sakthai/mcp.json`):
```json
{
  "servers": [
    { "name": "my-server", "command": "npx", "args": ["-y", "my-mcp-pkg"] }
  ]
}
```

### CLI subsystem (`cli/`)

Click commands split by area; all sub-files imported by `cli/__init__.py`:
- `agent.py` — `run`, `mcp`
- `memory.py` — `learn`, `recall`, `memory` group
- `system.py` — `doctor`, `setup`, `status`, `tools`
- `skills.py` — `skills` group
- `cycle.py` — `cycle` group
- `extensions.py` — `extensions` group
- `dashboard.py` — `dashboard` (launches Streamlit)
- `sessions.py` — `sessions` group
- `cloud.py` — `cloud` group (lazy import of `sakthai.cloud`)

### Other subsystems

- **`cycle/`** — six-stage Dream → Hope → Care → Joy → Trust → Growth state
  machine. `stages.py` defines the `Stage` enum; `state.py` persists the current
  stage as a single fact in the store (kind=`cycle`, key=`current_stage`).
- **`skills.py` + `skills/` + `library/`** — parse/catalog/validate `SKILL.md`
  files (YAML frontmatter: name, category, description, version, platforms, tags,
  related_skills). `library/` has 48 curated skills across 11 categories;
  `skills/` has 18 user/extension skills. Skills are injected into the agent
  system prompt via `render_skills_prompt_block()`.
- **`dashboard/`** — `data.py` builds a UI-free, testable snapshot of the store
  (KPIs, growth series, per-kind breakdown, date-range filtering). `app.py`
  renders it in Streamlit (tabs: Overview, Memory Explorer, Sessions, Cycle,
  Settings). `app.py` has loose mypy (`ignore_errors = true`).
- **`extensions/install.py`** — clones skill/MCP bundles from git into
  `~/.sakthai/extensions`; `list`/`remove` manage installed bundles.
- **`cloud/`** — lazy-import stub. `runtime.py` describes a cloud agent without
  importing `google-adk` at module load; `tools.py` adapts the memory surface as
  ADK function tools. Import gated behind the `cloud` extra.
- **`web/server.py`** — minimal HTTP server stub for a future web runtime.
- **`learn/capture.py`** — `learn()` one-shot fact capture used by `sakthai learn`.

---

## File structure

```
sakthai-agent-v2/
├── sakthai/                  # Main package
│   ├── config.py             # Paths & env-var names (single source of truth)
│   ├── auth.py               # Credential resolution
│   ├── skills.py             # Skill discovery, parsing, injection
│   ├── agent/
│   │   ├── loop.py           # run_agent() orchestration
│   │   ├── tools.py          # BUILTIN_TOOLS registry
│   │   ├── registry.py       # ToolRegistry class
│   │   ├── usage.py          # Token tracking
│   │   └── providers/        # Claude / Gemini / OpenAI / Ollama backends
│   ├── memory/
│   │   ├── store.py          # MemoryStore (only SQLite access)
│   │   ├── provider.py       # System-prompt adapter
│   │   ├── backup.py         # Timestamped db copy
│   │   └── sync.py           # Git/HTTP multi-agent sync
│   ├── mcp/
│   │   ├── server.py         # Inbound JSON-RPC stdio server
│   │   ├── client.py         # Outbound stdio client
│   │   ├── manager.py        # connect_servers() context manager
│   │   └── servers.py        # MCPServerSpec + spec discovery
│   ├── cli/                  # Click commands (agent, memory, system, ...)
│   ├── cycle/                # Dream→Hope→Care→Joy→Trust→Growth state machine
│   ├── learn/                # capture.py one-shot fact entry
│   ├── extensions/           # install.py (git-based bundle installer)
│   ├── dashboard/            # data.py (snapshot) + app.py (Streamlit)
│   ├── cloud/                # Lazy ADK/Vertex stub (cloud extra)
│   └── web/                  # HTTP server stub
├── tests/                    # 33 test files, hermetic, no network
├── skills/                   # 18 user/extension SKILL.md folders
├── library/                  # 48 curated skills in 11 categories
├── docs/                     # Architecture & design docs
├── scripts/                  # Dev utilities (not linted/type-checked)
├── data/                     # Sample memory exports (JSONL/CSV)
├── pyproject.toml            # Build config, deps, tool settings
└── uv.lock                   # Locked deps (used by CI)
```

---

## Tests

Tests live in `tests/` (33 files, ~8400 lines). All tests are hermetic — no
network, no GCP credentials. Integration tests that may hit real endpoints
(Ollama, Anthropic) are marked `@pytest.mark.integration` and self-skip when
credentials/endpoints are absent; CI excludes them with `-m "not integration"`.

Key test areas:
- `test_memory_store.py`, `test_memory_sync.py`, `test_memory_aux.py`,
  `test_memory_concurrent.py`, `test_store_migrations.py` — memory subsystem
- `test_agent_loop.py`, `test_tools.py`, `test_registry.py`, `test_usage.py`,
  `test_providers_*.py` (4 files) — agent subsystem
- `test_mcp_server.py`, `test_mcp_client.py`, `test_mcp_manager.py`,
  `test_mcp_servers.py` — MCP subsystem
- `test_cli*.py`, `test_sessions_cli.py` — CLI commands
- `test_dashboard_data.py`, `test_dashboard_app.py`, `test_dashboard_sessions.py`
- `test_auth.py`, `test_config_reports.py`, `test_extensions.py`,
  `test_skill_injection.py`, `test_cycle_skills_config.py`, `test_cloud.py`,
  `test_integration.py`, `test_web_server.py`
- `conftest.py` — shared fixtures: in-memory `MemoryStore`, temp dirs,
  mock Anthropic clients

**Pattern for new tests:** inject a fresh `MemoryStore(":memory:")` (SQLite
in-memory); mock the Anthropic/Gemini/OpenAI client at the boundary; never
reach out to a real endpoint. Use `tmp_path` fixtures for file I/O.

---

## Conventions specific to this repo

- **The memory store is the seam.** Anything touching SQLite goes through
  `MemoryStore`; anything an agent or MCP client can do goes through the
  `agent/tools.py` registry. Don't bypass either.
- **Config centralization.** No module hard-codes a path — everything goes through
  `config.py`. New paths and env-var names belong there.
- **Dependency injection over global state.** `run_agent()` and `handle_request()`
  accept injectable client and store arguments; this is what makes them testable.
  Don't use module-level globals for these.
- **Tests assume no network and no GCP credentials.** Keep them hermetic; inject
  clients/stores instead of reaching out.
- **Sandbox defaults are deliberate.** `read_file` is restricted to cwd +
  `~/.sakthai` + `SAKTHAI_READ_ALLOW`; `run_command` is **opt-in** via
  `SAKTHAI_SHELL_ALLOW`. Don't widen these without reason.
- **Not linted / not type-checked:** ruff excludes `library/` and `scripts/`;
  mypy only covers `sakthai/`. Don't "fix" lint/types in those trees.
- **mypy is `strict`** over `sakthai/` (`dashboard/app.py` is the one exception:
  `ignore_errors = true`). Keep all new code strict-clean.
- **Schema migrations are additive.** Use `ALTER TABLE` only, under
  `BEGIN IMMEDIATE`. Never drop columns or tables in a migration.
- **Tool registry is the MCP server.** `BUILTIN_TOOLS` in `agent/tools.py` is
  the single definition; `mcp/server.py` reuses it directly. Add a tool once and
  it appears in both surfaces.
- **Later tool wins on name clash.** In `ToolRegistry.with_tools()`, a plugin or
  external MCP server tool can shadow a built-in by registering under the same
  name.
- **Ollama uses 127.0.0.1, not localhost.** IPv6 resolution for `localhost` breaks
  some environments; the OpenAI provider explicitly connects to `127.0.0.1`.
- **Cloud module imports are lazy.** `sakthai/cloud/` never imports `google-adk`
  at module load — only inside functions, guarded by try/except ImportError.

---

## Key environment variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic auth for `sakthai run` / `mcp` (or `ANTHROPIC_AUTH_TOKEN`, or Claude CLI OAuth) |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Gemini auth (or Gemini CLI OAuth token) |
| `OPENAI_API_KEY` | Key for OpenAI-compatible gateway (defaults to `nokey`) |
| `OPENAI_API_BASE` / `OPENAI_BASE_URL` | Base URL for OpenAI-compatible endpoint |
| `OLLAMA_HOST` | Ollama server address (default: `http://127.0.0.1:11434`) |
| `SAKTHAI_HOME` | Override the `~/.sakthai` root (memory db, sessions, extensions) |
| `SAKTHAI_READ_ALLOW` | Colon-separated extra paths the `read_file` tool may read |
| `SAKTHAI_SHELL_ALLOW` | Any non-empty value enables the `run_command` tool |
| `SAKTHAI_MCP_TIMEOUT` | Seconds to wait for an external MCP server reply (default: 30) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Needed for the `send_telegram_message` tool |

---

## Skills format

A skill is a directory containing a `SKILL.md` with a YAML frontmatter block:

```yaml
---
name: my-skill
category: coding
description: One-line summary of what this skill does
version: "1.0"
platforms: [claude, gemini]
tags: [python, testing]
related_skills: [other-skill]
---

Skill body goes here. This is injected into the agent system prompt when the
skill is active.
```

Skills are discovered from `skills/` (user/extension skills) and `library/`
(curated catalog). Run `sakthai skills list` to see all discovered skills.

---

## Adding a new built-in tool

1. Add a `Tool(name=..., description=..., input_schema=..., handler=...)` to
   `BUILTIN_TOOLS` in `sakthai/agent/tools.py`.
2. The tool automatically appears in both `sakthai run` (agent loop) and
   `sakthai mcp` (MCP server) — no other wiring needed.
3. Write a test in `tests/test_tools.py` using an injected `MemoryStore(":memory:")`.
4. If the tool touches the filesystem or network, sandbox it appropriately
   (follow the `read_file` / `run_command` patterns).

---

## Docs

| File | Contents |
|------|---------|
| `docs/architecture.md` | Full layer diagram and SQLite schema |
| `docs/capabilities.md` | Feature list |
| `docs/cloud.md` | Google ADK / Vertex AI deployment stub |
| `docs/plugins.md` | Skills and MCP extensibility |
| `docs/replication.md` | Multi-agent memory sync |
| `docs/runtimes.md` | CLI / agent loop / MCP server / cloud |
| `docs/workspace.md` | Dev environment setup |
| `docs/og_parity_audit.md` | Comparison with original SakThai |
