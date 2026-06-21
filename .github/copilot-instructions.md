# Copilot instructions for sakthai-agent-v2

Purpose
- Quick, focused guidance for Copilot/CLI assistants working in this repository.
- Consult these files for deeper context: README.md, CLAUDE.md, GEMINI.md, CONTRIBUTING.md and docs/*.

1) Build, test, and lint (commands)
- Install (preferred, reproducible):
  - uv sync --all-extras
  - or: pip install -e ".[dev]" (dev toolchain)
  - optional dashboard extras: pip install -e ".[dashboard]"

- Full test suite (hermetic):
  - python -m pytest tests/ -q

- Run a single test file (example):
  - python -m pytest tests/test_memory_store.py -q

- Exclude integration tests (CI default):
  - python -m pytest -m "not integration" -q

- Lint / format / types / security (mirror CI):
  - ruff check sakthai tests
  - ruff format --check sakthai tests
  - mypy sakthai
  - bandit -c pyproject.toml -r sakthai

- Notes:
  - CI runs on Python 3.11–3.13 and requires green lint + tests before merging.
  - Coverage floor: fail_under = 85 (tool.coverage.report in pyproject.toml).

2) High-level architecture (big picture)
- One package, three ways in: CLI (sakthai), Agent loop (sakthai run "task"), MCP stdio server (sakthai mcp).
- Data flow: CLI / MCP -> agent loop -> tool registry (sakthai/agent/tools.py) -> MemoryStore (sakthai/memory/store.py) -> SQLite DB (~/.sakthai/memory.db; override with SAKTHAI_HOME).
- Core subsystems:
  - memory/: MemoryStore is the single SQLite seam; provider adapter injects memory into prompts.
  - agent/: run_agent orchestration, tool registry, and providers (Anthropic/Gemini/OpenAI/Ollama).
  - mcp/: inbound JSON-RPC stdio server and outbound client/manager for external MCP servers.
  - cli/: Click commands that surface the tools and runtimes.
  - skills/ & library/: SKILL.md-based skills injected into the system prompt.
- Entry points share the same tool registry: add a tool once (agent/tools.BUILTIN_TOOLS) and it appears in both agent loop and MCP.

3) Key repository conventions (do not deviate)
- Memory store is the seam: all SQLite access must go through sakthai/memory/store.py (MemoryStore).
- Config centralization: use sakthai/config.py for paths and env-var names; do not hard-code paths.
- Dependency injection: run_agent() and mcp.handle_request()/manager accept injectable client/store arguments — prefer DI for testability; avoid module-level globals for clients/stores.
- Tests are hermetic: no network or GCP credentials. Mark integration tests with @pytest.mark.integration; they self-skip when credentials are absent. Use MemoryStore(":memory:") and tmp_path fixtures.
- Sandbox defaults: read_file limited to cwd + ~/.sakthai + SAKTHAI_READ_ALLOW; run_command is opt-in via SAKTHAI_SHELL_ALLOW. Respect these guards.
- Tool registry is authoritative: add new tools to sakthai/agent/tools.py (BUILTIN_TOOLS) and write tests in tests/test_tools.py using an injected MemoryStore.
- Later tool wins: ToolRegistry.with_tools() allows external plugins/MCP servers to shadow built-ins by name.
- Schema migrations: migrations are additive (ALTER TABLE only), run under BEGIN IMMEDIATE; never drop columns/tables in a migration.
- Lint/type scope: ruff excludes library/ and scripts/; mypy only checks sakthai/ (dashboard/app.py is ignored). Keep new code strict-clean.
- Ollama networking: prefer 127.0.0.1 (not localhost) for Ollama hosts to avoid IPv6 resolution issues.

4) Important files to consult
- README.md, CLAUDE.md, GEMINI.md (project-specific assistant guidance).
- CONTRIBUTING.md (quality bar, CI gates, test examples).
- docs/architecture.md, docs/plugins.md, docs/runtimes.md (detailed diagrams and flows).
- sakthai/agent/tools.py (BUILTIN_TOOLS) and sakthai/memory/store.py (MemoryStore) — the two critical seams.

5) Test & dev patterns
- New tests: inject MemoryStore(":memory:") and mock provider clients at the provider boundary; keep tests hermetic.
- Use git worktrees for isolated development if multiple agents/devs share the checkout (see CONTRIBUTING.md).

6) AI assistant configs
- This repo contains CLAUDE.md and GEMINI.md. Copilot sessions should read them before making repo-wide recommendations.

7) When editing code
- Make surgical edits only. Validate with ruff, mypy, bandit, pytest locally before suggesting a PR. Update docs (README, docs/, CLAUDE.md) if behavior or conventions change.

Maintainer note
- Created from README.md, CLAUDE.md, CONTRIBUTING.md and pyproject.toml.


---

MCP servers — example config

Add a JSON file at ~/.sakthai/mcp.json (or under SAKTHAI_HOME) to declare external MCP servers. Example entries below can be dropped into that file or used as a starting point for local development.

Example (Hermes + Ollama):

{
  "servers": [
    {
      "name": "hermes",
      "command": "hermes",
      "args": ["mcp", "serve"],
      "env": {}
    },
    {
      "name": "ollama",
      "command": "ollama",
      "args": ["mcp", "serve"],
      "env": {}
    }
  ]
}

Notes & tips:
- Hermes: installs/tools vary by Hermes distribution; the example exposes Hermes tools under the `hermes__*` namespace in SakThai.
- Ollama: when used as a provider prefer OLLAMA_HOST=http://127.0.0.1:11434 (IPv4 literal avoids localhost/IPv6 issues).
- GitHub-style npx MCP server example:

{
  "servers": [
    {
      "name": "github",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token-here" }
    }
  ]
}

How SakThai uses these specs:
- On `sakthai run`, SakThai auto-loads ~/.sakthai/mcp.json and attempts to start each server, merging their tools into the registry as `<server>__<tool>`.
- Use `sakthai status` or `sakthai status | sakthai tools` to list discovered tools.
- Pass `--no-mcp` to `sakthai run` to disable MCP discovery.

Would you like me to also add a docs/example file in the repo (docs/example-mcp.json) with these entries?"}