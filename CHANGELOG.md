# Changelog

All notable changes to `sakthai-agent` (v2) are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog covers the v2 clean-room rewrite only. The original
`SakThai-Agent` (v1) is a locked, archived blueprint and its history is not
carried forward here.

## [Unreleased]

### Changed
- License posture is now **all rights reserved** (© 2026 beer-sakthai). The
  `LICENSE` file (MIT) was removed and README, `pyproject.toml`, `SECURITY.md`,
  and `CODE_OF_CONDUCT.md` were updated to match the source-available,
  no-redistribution terms.

### Added
- Identity & governance docs re-derived for v2: `SAKTHAI.md`, `CODE_OF_CONDUCT.md`,
  and this `CHANGELOG.md`.
- OG→v2 information-parity audit (`docs/og_parity_audit.md`) recording keep/drop
  decisions for the v1 skills, library corpus, and code modules.
- Workflows & caveman integration audit (`docs/workflows_caveman_integration_audit.md`).
- Unified extension discovery across `~/.sakthai/extensions` and `~/.gemini/extensions`.

### Removed
- **Cloud runtime skeleton** — the lazy `sakthai/cloud/` Google ADK / Vertex AI
  scaffolding, the `cloud` install extra, the `sakthai cloud` commands, the
  `GOOGLE_CLOUD_*` / `GOOGLE_GENAI_USE_VERTEXAI` config helpers, and `docs/cloud.md`.
  v2 is local-first; a cloud port is no longer tracked here.

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
All notable changes to the `sakthai-agent-v2` project will be documented in this file.

---

## [2.2.0] — 2026-06-17
### Added
- **Unified Extension Paths**: Integrated automatic discovery of skills and MCP servers installed under the user's `~/.gemini/extensions/` path.
- **Namespaced Slash Commands**: Support for parsing and routing namespaced extension commands (e.g. `/plugin:command`) natively within the agent loop.
- **Caveman Mode Toggle**: Added `--caveman [lite|full|ultra]` flag to `sakthai run` to dynamically compress assistant output and save tokens.
- **User Preference Rules**: Copied user tone/style preference rules to `sakthai-personal` skill.

---

## [2.1.0] — 2026-06-16
### Added
- **Fast-Track Mode**: `--fast` flag to bypass the 6-stage verification cycle.
- **Memory Sync**: Remote memory backup and sync (`sakthai memory sync`) via Git and zero-dependency HTTP fallbacks.
- **Incremental Exports**: Transitioned snapshot generation to `facts.jsonl` and `observations.jsonl`.
- **Auto-Merge Conflict Resolver**: Local SQLite DB-based merge resolution during Git synchronizations.

---

## [2.0.0] — 2026-06-15
### Added
- **Stdio MCP Client**: Dynamic integration with external stdio-based MCP servers.
- **Provider Refactoring**: Split loops and moved Anthropic, OpenAI, Gemini, and Ollama providers to isolated package modules.
- **Streaming Output**: Native `--stream` token display.
- **Streamlit Activity Dashboard**: Session activity timelines and model token utilization statistics.
