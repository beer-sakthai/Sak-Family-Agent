# Changelog

All notable changes to `sakthai-agent` (v2) are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog covers the v2 clean-room rewrite only. The original
`SakThai-Agent` (v1) is a locked, archived blueprint and its history is not
carried forward here.

## [Unreleased]

### Added
- Identity & governance docs re-derived for v2: `SAKTHAI.md`, `CODE_OF_CONDUCT.md`
  (MIT-aligned), and this `CHANGELOG.md`.
- OG→v2 information-parity audit (`docs/og_parity_audit.md`) recording keep/drop
  decisions for the v1 skills, library corpus, and code modules.
- Workflows & caveman integration audit (`docs/workflows_caveman_integration_audit.md`).
- Unified extension discovery across `~/.sakthai/extensions` and `~/.gemini/extensions`.

## [2.0.0]

First release of the clean-room rewrite. A personal learning agent with a
durable SQLite memory exposed three ways — the `sakthai` CLI, the `sakthai run`
agent loop, and the `sakthai mcp` stdio server — all sharing `~/.sakthai/memory.db`.

### Added
- **Persistent memory** — `MemoryStore` over SQLite (WAL mode, `BEGIN IMMEDIATE`
  writes) holding facts and observations with search, tagging, dedupe,
  consolidation, stats, and snapshot import/export. Additive-only schema
  migrations.
- **Shared tool registry** — `agent/tools.py` defines the built-in tools once;
  `ToolRegistry` (`agent/registry.py`) serves both the agent loop and the MCP
  server with last-wins merge for runtime-discovered tools.
- **Agent loop** — provider-agnostic tool-using loop (`agent/loop.py`) with
  injectable client/store, session logging, retry with exponential backoff,
  token-usage tracking, indirect-recursion guard, context pruning, and a
  zero-cost `sakthai run --dry-run` preflight.
- **Providers** — Anthropic, Google Gemini, and any OpenAI-compatible/Ollama
  endpoint, extracted into `agent/providers/`. Streaming output via an `on_token`
  callback (`sakthai run --stream`) for Anthropic and OpenAI-compatible SSE.
- **MCP server** — dependency-free JSON-RPC 2.0 stdio server (`mcp/server.py`)
  with a pure `handle_request`.
- **Outbound MCP** — discover and connect external MCP servers
  (`mcp/{client,manager,servers}.py`); their tools merge into a run, namespaced
  `<server>__<tool>`, failing soft. Auto-loaded from `~/.sakthai/mcp.json`;
  opt out with `--no-mcp`.
- **Skill injection** — render selected `SKILL.md` bodies into the system prompt
  (`sakthai run --with-skills`), collected from bundled, library, and extension roots.
- **6-stage cycle** — Dream → Hope → Care → Joy → Trust → Growth state machine
  persisted as a single fact; `--fast` mode bypasses it for simple runs.
- **Memory sync** — `sakthai memory sync` with Git-backed remote, incremental
  `facts.jsonl` / `observations.jsonl` exports, id-based auto-merge of conflicts,
  and a zero-dependency `--http-url` POST fallback.
- **Dashboard** — UI-free snapshot layer (`dashboard/data.py`) plus a Streamlit
  app with Memory and Agent Activity tabs (session timeline, token usage by
  model, recent runs). `dashboard --export` writes JSON with no extra deps.
- **Cloud runtime skeleton** — lazy `sakthai/cloud/` scaffolding (`cloud` extra,
  `sakthai cloud` commands) that describes/scaffolds a deployment without
  importing `google-adk` at module load.
- **Tooling & CI** — `uv`-managed deps with `uv.lock`; CI runs gitleaks → ruff →
  ruff format → mypy (strict over `sakthai/`) → bandit → pytest (hermetic,
  `-m "not integration"`) on Python 3.11 and 3.12.

[Unreleased]: https://github.com/beer-sakthai/sakthai-agent-v2/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/beer-sakthai/sakthai-agent-v2/releases/tag/v2.0.0
