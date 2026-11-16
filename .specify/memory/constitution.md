# House of Sak Constitution

## Core Principles

### I. Test-First & 96% Coverage Floor (NON-NEGOTIABLE)
All development across the House of Sak monorepo follows strict Test-Driven Development (TDD). The test suite (`make test` / `pytest`) enforces a mandatory coverage floor of 96% (`--cov-fail-under=96`) on the core package (`personas/sakthai/`). Every new feature, CLI subcommand, agent loop seam, MCP server integration, and memory routine must arrive with dedicated unit tests in `tests/`. Any commit dropping test coverage below 96% fails continuous integration immediately.

### II. Canonical Package Structure & Explicit Module Resolution
The installable core package lives strictly at `personas/sakthai/` — not at the repository root. There is no root-level `sakthai/` package.
1. The package is editable-installed via `uv sync --all-extras`.
2. Any standalone helper, automation script, or maintenance tool in `scripts/` or `personas/` that imports `sakthai` must insert the canonical package path explicitly:
   `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))`.
3. Personas reside in isolated subdirectories (`personas/<agent>/`) sharing common core infrastructure while maintaining distinct identities (`SOUL.md`), configurations, and memory boundaries.

### III. Local-First Memory Isolation & Multi-Agent Consistency
Each of the 6 Sak Family personas (`SakThai`, `SakKing`, `SakSee`, `SakSit`, `SakJules`, `SakTan`) maintains a local-first SQLite memory database rooted at `~/.sakthai/<name>/memory.db` (or `$SAKTHAI_HOME`).
1. Raw direct mutations to SQLite databases are strictly forbidden. All state mutations must pass through `MemoryStore` or the `sakthai memory` CLI.
2. Cross-agent context sharing must occur via designated multi-persona interfaces (`sakthai memory family`) and structured memory tags (e.g., `charge-report`, `schedule-confirmed`, `data-request`).

### IV. Pipeline Discipline & CI/CD Gatekeeping
In accordance with SakJules automation protocols:
1. Always inspect open pull requests (`gh pr list`) before starting work or submitting a PR to prevent duplicate fixes and conflicting patches.
2. Every pull request must pass the automated quality gates:
   - `make lint` (Ruff formatting & linting with 100-character line limit)
   - `uv run mypy personas/sakthai` (Strict type checking)
   - `uv run bandit -c pyproject.toml -r personas/sakthai` (AST security analysis)
   - `make test` (Full pytest test suite meeting >= 96% coverage)
3. Branches must be rebased onto the latest `main` before merging.

### V. Zero-Leak Security & Defense-in-Depth
1. Secrets, provider API keys (`HF_TOKEN`, Anthropic/Gemini/OpenAI credentials), and sensitive session tokens must never be committed to source control.
2. All commits and pull requests are checked by Gitleaks and Bandit.
3. Security remediations and vulnerability fixes take immediate operational priority and must include dedicated regression tests.

## Multi-Agent Architecture & Persona Boundaries

1. **SakThai (`@sakthai_agent_bot`)**: Lead orchestrator, Hugging Face Hub master, architecture lead.
2. **SakKing (`@sakking_agent_bot`)**: General assistant, test runner, deputy 1.
3. **SakSee (`@saksee_agent_bot`)**: Web browsing, browser specialist, external research, deputy 3.
4. **SakSit (`@saksit_agent_bot`)**: Social, community engagement, content and card copy specialist.
5. **SakJules (`@sakjules_agent_bot`)**: CI/CD, GitHub automation, pipeline reliability, quality gatekeeper.
6. **SakTan (`@saktan_agent_bot`)**: Daily operations, scheduling, rhythm, local Ollama execution, deputy 2.

Cross-agent collaboration must respect persona domains; no persona should unilaterally modify or compromise another persona's core state without coordination.

## Specification & Planning Workflow

1. **Spec-First Specification**:
   New features should begin with a structured specification defining prioritized user stories (P1, P2, P3...) with independent testability and Given-When-Then acceptance criteria.
2. **Plan Alignment**:
   Feature work must be registered in `PLAN.md` before coding begins (`[ ]` -> `[/]`), and marked complete (`[x] YYYY-MM-DD`) only after all quality checks pass.
3. **Traceable Tasks**:
   Complex multi-step changes must be decomposed into ordered, verifiable tasks (`tasks.md`).

## Governance

This Constitution supersedes informal practices and represents the ratified architectural contract of the House of Sak monorepo.
- Any amendment to these principles requires documentation, user/maintainer approval, and corresponding test invariant updates.
- Pull requests and code reviews must verify compliance with this Constitution before merge approval.

**Version**: 1.0.0 | **Ratified**: 2026-11-16 | **Last Amended**: 2026-11-16
