# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`sakthai-agent` **v2.0** — a personal learning agent with persistent memory. It
gives a Claude or Gemini agent a durable SQLite memory it can read and write
across sessions, plus a shared tool registry and an MCP stdio server so the same
memory is reachable from other runtimes.

This is a **clean, from-scratch rewrite** of the original `SakThai-Agent` (the
"OG"). The OG is a read-only blueprint: consult it for intent, but never copy its
code or layout into this repository — re-derive everything. The OG's Google
ADK / Vertex AI cloud agent is **not** part of v2: there is **no `app/` cloud
bundle, no `sync-app-package.sh` sync step, and no `sakthai/cloud/` module** here.
v2 is local-first — the CLI, the agent loop, and the MCP stdio server.

## Monorepo Structure

The repository is the shared source workspace for the Sak family with these key conventions:

- **Canonical package:** `personas/shared/sakthai/` (single copy, symlinked from all personas)
- **Personas:** six agents on disk (`SakThai`, `SakKing`, `SakSee`, `SakSit`, `SakJules`, `SakTan`; also `config.PERSONA_NAMES`); **SakThai is lead**.
  - Each has `/skills/` with `Sak<Name>-*` prefixed skills, one directory per skill directly
    under `skills/` (no category subdirectories, no duplicate-named skill folders).
    `sakthai/skills/.archive/` is an intentional exception — retired skills kept for history,
    excluded from discovery. A skill directory may itself contain a documented "umbrella"
    sub-skill (see `SakThai-environment-automation`'s `cron-watchdog-self-heal`) accessed via
    direct file reads rather than the normal skill index.
  - Each has `/config/` with persona-specific config (config.yaml, mcp.json, gateway_voice_mode.json)
  - Each symlinks to `../shared/sakthai` and `../shared/agent-self-evolution`
- **Shared resources:** `personas/shared/` contains sakthai (Python package), agent-self-evolution (template), skills (Sak-* shared skills), model_roster
- **Skill naming:** `Sak-` prefix for shared skills, `Sak<Name>-` for per-persona skills (enforced by `sakthai skills validate --naming`)
- **CI scope:** ruff/mypy/bandit/pytest/pylint scopes to `sakthai` core only; gitleaks scans everything (`.gitleaks.toml` allowlists persona docs)

Everything below this point describes the SakThai agent package itself.

---

## Commands

```bash
# Setup (Python >=3.11)
cp .env.example .env      # then fill in ANTHROPIC_API_KEY
uv sync --all-extras      # install all project and optional dependencies

# Test / lint / type-check / security (mirrors .github/workflows/ci.yml)
uv run pytest tests/ -q                      # full unit suite (no network, no GCP)
uv run pytest tests/test_memory_store.py -q  # a single test file
uv run pytest -m "not integration" -q        # Exclude network tests (default in CI)
uv run ruff check personas/sakthai/sakthai tests              # Lint
uv run ruff format --check personas/sakthai/sakthai tests     # Format check (drop --check to apply)
uv run mypy personas/sakthai/sakthai                          # Strict type-check
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai   # Security scan
make mutation                                # mutmut on core seam modules (slow, local-only, not in CI)
```

CI (`.github/workflows/ci.yml`, via `uv sync --all-extras`) runs: lint (ruff
check + format --check) → static analysis (mypy, bandit) → pytest with
coverage, across Python **3.11 and 3.12**. A separate `pylint.yml` workflow
runs pylint over the same `personas/sakthai/sakthai` + `tests` scope. A
`secret-scan.yml` workflow runs gitleaks (config: `.gitleaks.toml`) on pushes
to `main` and all PRs, and `dependency-audit.yml` runs pip-audit over
`uv.lock` weekly and on dependency changes. CodeQL runs via GitHub's *default
setup* (repo settings), so there is deliberately no `codeql.yml` — adding one
would conflict. **No smoke-test job is wired into any GitHub workflow**,
despite `.claude/skills/run-sakthai-agent-v2/driver.py` existing in the repo
— treat that as available tooling, not an enforced CI gate. Run the lint→pytest
sequence locally before pushing; green CI is the bar for `main`. Coverage
floor is **96%** (`fail_under = 96`, branch coverage included) over the whole
`sakthai/` package.

---

## Runtime entry points

One package, three ways in — all sharing `~/.sakthai/memory.db` by default
(override the root with `SAKTHAI_HOME`). On the VM deployment, each persona's
process sets its own `SAKTHAI_HOME=$HOME/.sakthai/$AGENT`, so each persona
naturally gets its own memory shard at `~/.sakthai/<persona>/memory.db`. For
local dev, pass `--persona <name>` to `learn`/`recall`/`run`/`chat`/`memory` to
get the same per-persona shard without setting `SAKTHAI_HOME` yourself — see
"Per-persona memory sharding" below.

1. **CLI** — `sakthai <cmd>` (entry point `sakthai.cli:main`). Commands:
   - Memory: `learn`, `recall`, `memory show|stats|search|export|import|backup|consolidate|consolidate-sessions|deduplicate|family`
     — all except `family`, `sync`, and `pull` accept `--persona <name>` to scope to that
     persona's own shard instead of the default unscoped `memory.db`; `family` merges across
     every persona's shard (or a `--personas a,b,c` subset) into one read-only view.
   - Agent: `run "<task>"` — key flags: `--provider`/`-p` (anthropic/google/openai/ollama/gateway/huggingface),
     `--model`, `--max-tokens`, `--max-iterations`, `--max-seconds`, `--with-skills <name>`
     (repeatable), `--no-mcp`, `--dry-run` (validate config, no API call), `--stream`, `--fast`
     (skip the 6-stage cycle), `--stateless` (don't load/append memory), `--caveman
     lite|full|ultra|wenyan-*` (token-compression skill), `--sandbox` (run inside the
     `Dockerfile.sandbox` container; only `memory.db` is bind-mounted; not combinable with
     `--persona`), `--persona <name>` (use that persona's memory shard + inject its SOUL.md
     as a system-prompt prefix), `-v/--verbose`
   - Server: `mcp` (start MCP stdio server)
   - Cycle: `cycle status|next|set|list`
   - Skills: `skills list|show|validate|create|sync-sakking`
   - Extensions: `extensions add|list|remove`
   - Sessions: `sessions list|show|export`
   - System: `doctor`, `setup`, `status`, `tools`
   - Eval: `eval` (inspect local model evaluation / MLOps metrics)
   - Hugging Face: `hf info|download <repo_id>`
   - Note: there is **no `dashboard` CLI command** — the CLI wiring was
     removed, but `sakthai/dashboard/data.py` (the KPI collection module used
     by `web/server.py`) was later re-added. See the dashboard note under
     "Other subsystems" below.

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
- **`sandbox.py`** — backs `sakthai run --sandbox`. Builds/reuses a Docker image
  from `Dockerfile.sandbox` (layer-cached) and re-executes the task inside it;
  only `memory.db` is bind-mounted from the host. Raises `SandboxError` if Docker
  isn't on `PATH`.

### Memory subsystem (`memory/`)

- **`memory/store.py`** — `MemoryStore` is the **only** code that touches SQLite.
  It holds *facts* (`Fact` dataclass: `id`, kind, key, value, source_session,
  created_at, updated_at, tags) and *observations* (`Observation` dataclass: `id`,
  summary, evidence_session_id, weight, confidence, created_at). Features:
  WAL concurrency, additive migrations in `_migrate_schema()` (ALTER TABLE only,
  under `BEGIN IMMEDIATE`), snapshot export/import (JSONL/CSV), deduplicate, and
  consolidate. `render_prompt_block()` injects memory into the system prompt.
- **`memory/provider.py`** — `SakThaiMemoryProvider` adapts the store to
  system-prompt blocks with context-window limiting.
- **`memory/backup.py`** — timestamped copy of `memory.db`, or of an explicit
  `db_path` (used to back up a persona's own shard).
- **`memory/sync.py`** — git-based JSONL export/import (multi-agent sync) and
  HTTP backup to a configured endpoint.
- **`memory/merged.py`** — `FamilyMemoryView`, a read-only view across every
  persona's memory shard plus the legacy unscoped `memory.db`, deduplicated and
  grouped by persona. Backs `sakthai memory family`. See "Per-persona memory
  sharding" below.

### Per-persona memory sharding

Each of the six personas gets its own memory shard, `~/.sakthai/<persona>/memory.db`,
distinct from the legacy unscoped `~/.sakthai/memory.db`. This isn't a new
mechanism: it's the same convention already used in production by
`infra/vm-agents/sakthai-agent-run.sh`, which runs each deployed persona with
`SAKTHAI_HOME=$HOME/.sakthai/$AGENT` — `memory_db_path()` (which does honor
`SAKTHAI_HOME`) already resolved to that persona's shard for any process running
that way. What's new is `config.persona_memory_db_path(persona)`, which computes
the same `~/.sakthai/<persona>/memory.db` path directly from `Path.home()`,
**independent of the current process's own `SAKTHAI_HOME`**. That's what makes
two things possible that weren't before:

- **Local CLI parity** — `learn`/`recall`/`run`/`chat`/`memory <subcommand>` all
  accept `--persona <name>` so a local dev shell (which isn't running with a
  persona-scoped `SAKTHAI_HOME`) can still read/write a specific persona's shard,
  and `run --persona`/`chat --persona` also inject that persona's `SOUL.md` as a
  system-prompt prefix. `memory sync`/`memory pull` reject `--persona` (they
  always target the unscoped `memory.db` — no per-persona git/HTTP sync exists).
  `run --persona` can't combine with `--sandbox` (the sandbox only bind-mounts
  the unscoped `memory.db`).
- **The merged family view** — `FamilyMemoryView` (`memory/merged.py`) opens
  every persona's shard (skipping ones that don't exist yet) plus the legacy
  `memory.db` at once, regardless of which single persona the current process
  would otherwise be scoped to, and merges/dedups facts and observations across
  them. `sakthai memory family [--personas a,b,c] [--limit N] [--json]` is the
  CLI surface for it.

A persona's shard file only comes into existence on first write (`learn
--persona X`, or any `run`/`chat --persona X` that calls a memory-writing
tool) — an unwritten-to persona is simply absent from `memory family` output,
not an error.

### Agent subsystem (`agent/`)

- **`agent/tools.py`** — defines `BUILTIN_TOOLS` (10 tools, one schema + handler
  each): `learn`, `ingest_document`, `capture_lead`, `recall`, `search`, `forget`,
  `read_file`, `run_command`, `send_telegram_message`, `run_agent_loop`. Add a
  tool here and it appears in both the agent loop and the MCP server
  automatically. Note: `run_agent_loop` is filtered out of the in-loop tool set
  (it's MCP-only) to avoid recursion.
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
  - `openai_provider.py` — OpenAI-compatible APIs, Ollama, the `gateway`
    provider (OpenRouter/LiteLLM/Vercel/Cloudflare AI gateways), and the
    `huggingface` provider (HF Inference Providers router, via `HF_TOKEN`) — all via `httpx`
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
- `eval.py` — `eval` (local model evaluation / MLOps metrics)
- `sessions.py` — `sessions` group
- `hf.py` — `hf info|download` (Hugging Face Hub operations)

There is no `dashboard.py` here — see the dashboard note below.

### Other subsystems

- **`cycle/`** — six-stage Dream → Hope → Care → Joy → Trust → Growth state
  machine. `stages.py` defines the `Stage` enum; `state.py` persists the current
  stage as a single fact in the store (kind=`cycle`, key=`current_stage`).
- **`skills.py` + `library/` + `personas/*/skills/`** — parse/catalog/validate
  `SKILL.md` files (YAML frontmatter: name, category, description, version,
  platforms, tags, related_skills). Default discovery roots
  (`default_skill_roots()` in `skills.py`) are: `personas/sakthai/skills/`
  (`SKILLS_DIR`, this persona's own overlay), `personas/shared/skills/`
  (`SHARED_SKILLS_DIR`/`LIBRARY_DIR`, 3 skills byte-identical across all
  personas), root `library/` (`CURATED_LIBRARY_DIR`, 31 curated skills across
  11 categories, pre-dates the `Sak-`/`SakThai-` naming convention), and
  `~/.sakthai/extensions`. The root-level `skills/` directory is **not** one
  of these roots — it's orphaned content, not part of live skill discovery.
  Skills are injected into the agent system prompt via
  `render_skills_prompt_block()`.
- **Dashboard — backend only.** The CLI's `dashboard` command and the
  frontend (both the old in-package bundle and the repo-root Vite project)
  are gone, but `personas/sakthai/sakthai/dashboard/data.py` was re-added:
  it collects KPI/lead/revenue metrics from the memory store and is served by
  `web/server.py`'s `/api/stages` endpoint (covered by
  `tests/test_dashboard_data.py`). `_STATIC_ROOT` resolves to
  `personas/sakthai/sakthai/dashboard/dist/`, which does not exist, so the
  web server runs API-only and static requests fall through to 403/404.
- **`extensions/install.py`** — clones skill/MCP bundles from git into
  `~/.sakthai/extensions`; `list`/`remove` manage installed bundles.
- **`web/server.py`** — HTTP API server; optionally serves a pre-built static
  bundle from `_STATIC_ROOT` (see the dashboard note above) alongside its API
  endpoints, falling back to 403/404 for static requests if it's missing.
- **`learn/capture.py`** — `learn()` one-shot fact capture used by `sakthai learn`.
- **`telegram/`** — a standalone `python-telegram-bot` polling bot (`bot.py`,
  `config.py`, `workflow_executor.py`) that shells out to
  `python -m sakthai run ... --with-skills <name> --fast --stateless` per
  `/workflow <name>` command. `telegram/config.py` re-exports
  `ALLOWED_USER_IDS`/`TELEGRAM_BOT_TOKEN` from the central `config.py`
  (`telegram_allowed_user_ids()`/`telegram_bot_token()`), and
  `workflow_executor.py` uses `config.SKILLS_DIR` rather than a hardcoded
  path — aligned with this repo's config-centralization convention. Covered
  by `tests/test_telegram_bot.py` and `tests/test_telegram_workflow_executor.py`.


---

## Tests

Tests live in `tests/` (90 files, ~21,500 lines). All tests are hermetic — no
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
- `test_auth.py`, `test_config_reports.py`, `test_extensions.py`,
  `test_skill_injection.py`, `test_cycle_skills_config.py`,
  `test_integration.py`, `test_web_server.py`
- `conftest.py` — shared fixtures: in-memory `MemoryStore`, temp dirs,
  mock Anthropic clients

**Pattern for new tests:** inject a fresh `MemoryStore(":memory:")` (SQLite
in-memory); mock the Anthropic/Gemini/OpenAI client at the boundary; never
reach out to a real endpoint. Use `tmp_path` fixtures for file I/O.

---

## Conventions specific to this repository

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
- **mypy is `strict`** over the whole `sakthai/` package with no per-module
  exceptions. Keep all new code strict-clean.
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

---

## Workflow: Plan First

- **Always read and update `PLAN.md` before starting any work** in this repository.
  - Mark tasks `[ ]` → `[/]` (in progress) at the start of a phase.
  - Mark `[/]` → `[x] YYYY-MM-DD` (done with date) once the work is verified.
- **Never start coding a phase until it is checked off in PLAN.md** as in-progress.
- Terse one-word or short user approvals like `process`, `go`, `do it`, `run` after a plan summary = explicit approval to execute all queued plan steps.

### PLAN.md Safety

- **Never overwrite `PLAN.md` entirely.** Use `multi_replace_file_content` with targeted chunk replacements only.
- When marking tasks complete, find and replace only the specific `- [ ]` or `- [/]` line(s) — not whole sections.
- After any edit to `PLAN.md`, immediately re-read it to verify the surrounding content is intact before continuing.

---

## Key environment variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic auth for `sakthai run` / `mcp` (or `ANTHROPIC_AUTH_TOKEN`, or Claude CLI OAuth) |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Gemini auth (or Gemini CLI OAuth token) |
| `OPENAI_API_KEY` | Key for OpenAI-compatible gateway (defaults to `nokey`) |
| `OPENAI_API_BASE` / `OPENAI_BASE_URL` | Base URL for OpenAI-compatible endpoint |
| `OLLAMA_HOST` | Ollama server address (default: `http://127.0.0.1:11434`) |
| `SAKTHAI_GATEWAY_URL` | Base URL of an OpenAI-compatible AI gateway (OpenRouter/LiteLLM/Vercel/Cloudflare) — enables the `gateway` provider |
| `SAKTHAI_GATEWAY_API_KEY` | Bearer token for the AI gateway (defaults to `nokey`) |
| `HF_TOKEN` | Hugging Face access token — used by `sakthai hf` and the `huggingface` provider |
| `SAKTHAI_HF_API_BASE` | Hugging Face Inference Providers router base URL (default: `https://router.huggingface.co/v1`) |
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
platforms: [linux, macos, windows]   # host OSes the skill supports
metadata:
  sakthai:
    tags: [python, testing]
    related_skills: [other-skill]
---

Skill body goes here. This is injected into the agent system prompt when the
skill is active.
```

Note: `tags`/`related_skills` must be nested under `metadata.sakthai` — a flat
top-level `tags:`/`related_skills:` is silently ignored by the parser in
`skills.py`.

Skills are discovered from `skills/` (user/extension skills),
`personas/shared/skills/` (the shared six-persona skills), and `library/`
(curated catalog). Run `sakthai skills list` to see all discovered skills.
`sakthai run --dry-run` validates `--with-skills` names and fails on
unresolved ones; a live run warns and skips them.

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
| `docs/plugins.md` | Skills and MCP extensibility |
| `docs/replication.md` | Multi-agent memory sync |
| `docs/runtimes.md` | CLI / agent loop / MCP server |
| `docs/workspace.md` | Dev environment setup |
| `docs/og_parity_audit.md` | Comparison with original SakThai |
| `docs/integrations.md` | Composio and cross-agent communication recipes |
| `docs/SECURITY.md` · `docs/security-hardening.md` | Security policy/architecture · audit findings, fixes, and the prevention pattern + regression test for each |
