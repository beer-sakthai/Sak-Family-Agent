# Changelog

All notable changes to `sakthai-agent` (v2) are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog covers the v2 clean-room rewrite only. The original
`SakThai-Agent` (v1) is a locked, archived blueprint and its history is not
carried forward here.

## [Unreleased]

### In Progress
- **Cross-Persona A2A Streaming**: Real-time gRPC/A2A token streaming between SakKing, SakSee, SakSit, SakTan, SakJules, and SakThai.
- **Distributed Memory Vector Mesh**: High-concurrency embedding sync across external Postgres/pgvector nodes.
  - Roadmap: [docs/superpowers/plans/](docs/superpowers/plans/)

### Documentation
- Enhanced onboarding guide with practical "Get Started" tasks
- Updated README with quick-start section and table of contents
- Clarified security vulnerability reporting procedures
- Added code review checklist to CONTRIBUTING.md

---

## [2.6.0] — 2026-08-19

### Added
- **120 Curated Skills & Antigravity Tooling**: Installed and curated top 120 AI agent skills across the House of Sak family, complete with automated YAML frontmatter verification (`docs/curated-skills-120.md`, `docs/curated-skills-120.json`).
- **Path Traversal & Control Character Guardrail**: Zero-tolerance ASCII control character (`\x00-\x1f\x7f`) and multiple-prefix (`@@`) rejection in `_resolve_and_validate_path` across all tool executors (`personas/sakthai/sakthai/agent/tools.py`, `sakthai-chat-cli`, `apps/agent_workflow_framework/agent_workflow/executor.py`, and `services/teams-copilot-mcp`).
- **Dashboard Telemetry & React 19 Parity**: Upgraded `apps/sak_agent_dashboard` with `AutoCyclePanel`, `MutationTestingPanel`, `SemanticCachePanel`, and `A2AServiceRegistry` with zero ESLint/React effect lifecycle warnings.
- **Token Metering & Billing Parity**: Modern PBKDF2 API key hashing with explicit `@overload` signatures and automated byte parity enforcement in `tests/test_shared_package_divergence.py`.

### Changed
- **CI/CD Hardening & SHA Pinning**: Pinned all GitHub Actions dependencies to immutable commit SHAs with StepSecurity best practices, strict 20m timeouts, and top-level concurrency groups.
- **Dependency & Build Matrix 100% Green**: Achieved 100% green status across all 12 GitHub Actions workflows on Python 3.11 and Python 3.12.

---

## [2.5.0] — 2026-08-14

### Added
- **CodeQL Advanced SAST**: Multi-language code scanning across Actions, JavaScript/TypeScript, and Python with custom queries and SARIF reporting.
- **AST Mutation Testing & Self-Healing Gate**: Integrated mutation testing pipelines and self-healing test generation for surviving code mutants (`mutation-self-healing-gate.yml`).
- **Quality Flywheel Gate**: Automated multi-persona G-Eval benchmark measuring agent alignment, safety adherence, and task accuracy (`quality-flywheel-gate.yml`).

### Changed
- **Consolidated Dependabot Updates**: Unified multi-ecosystem update automation for pip (uv), npm/pnpm, Docker, and GitHub Actions under `.github/dependabot.yml`.

---

## [2.4.0] — 2026-08-08

### Added
- **Extended Test Suite & 96% Coverage Floor**: Expanded unit suite to 3,875+ tests with a strictly enforced 96% branch coverage gate.
- **Shared Persona Package Divergence Registry**: Automated regression suite detecting drift between core `sakthai` and persona overlay packages (`tests/test_shared_package_divergence.py`).

---

## [2.3.0] — 2026-07-20

### Added
- **Agent Self-Evolution Subsystem**: Independent self-evolution framework under `personas/sakthai/agent-self-evolution/` for continuous capability synthesis.
- **Teams Copilot MCP Server**: Added high-security Microsoft Teams Copilot bridge in `services/teams-copilot-mcp/`.

---

## [2.2.0] — 2026-06-17

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
