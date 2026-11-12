# Changelog

All notable changes to `sakthai-agent` (v2) are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog covers the v2 clean-room rewrite only. The original
`SakThai-Agent` (v1) is a locked, archived blueprint and its history is not
carried forward here.

## [Unreleased]

> This changelog has lagged the repository. The entries below cover the early
> v2 rewrite; the bulk of what landed since — the six-persona layout, per-persona
> memory sharding, the guardrails hardening rounds, the dashboard web API — is
> recorded in `PLAN.md`'s status table and the dated audits under `docs/`
> rather than here.

### Changed
- License posture is now **all rights reserved** (© 2026 beer-sakthai). The MIT
  terms were replaced: `LICENSE` now carries the House of Sak Intellectual
  Property License (source-available, no redistribution), and README,
  `SECURITY.md`, and `CODE_OF_CONDUCT.md` were updated to match. Note
  `pyproject.toml` currently declares no `license` field at all.

### Added
- Machine-readable `sakthai doctor --json` and `sakthai status --json` reports
  with deterministic, secret-free diagnostics and readiness exit codes.
- Built-in tools beyond the original set: `ingest_document`, `capture_lead`,
  `search_sessions`, the four Microsoft Graph mail/calendar tools,
  `run_agent_loop`, `family_recall`, `family_search`, and
  `delegate_to_persona` — 18 in total.
- `sakthai team` (declarative multi-agent pipelines) and `sakthai client`
  (ServiceQuoteBot provisioning) CLI groups.
- Dashboard HTTP API: `/api/personas`, `/api/metrics`, `/api/sessions`,
  `/api/memory`, `/api/audit`, `/api/workflows`, shaped by `web/contracts.py`
  and consumed by `apps/sak_agent_dashboard/`.
- Identity & governance docs re-derived for v2: `SAKTHAI.md`, `CODE_OF_CONDUCT.md`,
  and this `CHANGELOG.md`.
- OG→v2 information-parity audit (`docs/og_parity_audit.md`) recording keep/drop
  decisions for the v1 skills, library corpus, and code modules.
- Workflows & caveman integration audit (`docs/workflows_caveman_integration_audit.md`).
- Unified extension discovery across `~/.sakthai/extensions` and `~/.gemini/extensions`.
- Unified Agent Integration Platform (`sakthai.agent_platform`) — integrated modules for accidental data loss prevention (`safety.py`) with HMAC approval bypass, reactive Python dependency manager detection (`dep_manager.py`), progressive disclosure customizations (`customizations.py`), Jules remote asynchronous task delegation (`jules_worker.py`), dual Antigravity/ADK execution engine (`agent_engine.py`), and Harness AI agent pipeline spec generator (`harness_exporter.py`).
- Added `sakthai platform` CLI group (`detect-deps`, `check-safety`, `skills`, `export-harness`, `antigravity`), expanded dangerous command detection (`git reset --hard`, `git clean -f`, `mkfs`, `dd`, `terraform destroy`, `kubectl delete ns/all`), tracked `GEMINI.md`, and updated architecture & capabilities documentation with 39 unit tests achieving 99.5% coverage.
- Integrated Google Antigravity SDK (`google-antigravity>=0.1.23`) optional dependency and lockfile (`uv.lock`), with standalone agent runner `AntigravityAgentRunner` (`antigravity_agent.py`), standalone runner script `scripts/antigravity_agent.py`, `sakthai platform antigravity` CLI command, dynamic backend selection (Gemini hosted, LiteRT on-device, and local Ollama), and 49 unit tests achieving 99.6% coverage.
- Production Pro-Tips for `Sak-Family-Agent`:
  - **Safety Interception**: Integrated `check_data_loss_guardrail` in `sakthai.agent.guardrails_hardened` with `create_pre_execution_guardrail_hardened` to prevent destructive operations unless authorized by digest approval tokens.
  - **Progressive Disclosure for Skills**: Added `render_skills_progressive_summary` in `sakthai.skills` to generate lightweight metadata markdown tables, eliminating prompt bloat while allowing agents to load skills on demand.
  - **Model Selection Presets**: Added `ModelTier` (`fast`, `reasoning`, `local`, `lead`), `ModelPreset`, and `resolve_model_preset` in `sakthai.agent_platform.agent_engine`, integrated with `UnifiedAgentConfig` and `sakthai platform antigravity --tier`.
  - **Environment Introspection**: Added `wrap_with_isolated_runner` in `sakthai.agent_platform.dep_manager` to automatically wrap execution commands with the detected virtual environment package manager, exposed via `sakthai platform wrap-cmd`.
  - Added 27 unit tests in `tests/test_agent_platform_protips.py` achieving 98.5% branch coverage across the platform suite.

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
