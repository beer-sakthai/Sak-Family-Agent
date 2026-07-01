# Repository Guidelines

## Project Structure & Module Organization

This repository is the `sakthai-agent` v2 codebase: a local-first personal learning agent with persistent SQLite memory, shared tools, skills, and an MCP server. Core Python code lives in `sakthai/`, grouped by feature (memory, agent, MCP, dashboard, CLI). Tests live in `tests/` and should stay hermetic. Shared skills are in `skills/` and `library/`, docs in `docs/`, operational helpers in `scripts/`, and infra assets in `infra/`. The `dashboard/` directory contains the Streamlit UI, while `packages/agent-self-evolution/` is a separate Python package.

## Build, Test, and Development Commands

- `uv sync --all-extras`: install Python environment from `uv.lock`.
- `sakthai doctor`: check environment, config, and memory health.
- `sakthai setup`: validate `.env` and required secrets.
- `python -m pytest tests/ -q`: run the unit suite.
- `ruff check sakthai tests`: lint the core package and tests.
- `ruff format --check sakthai tests`: verify formatting.
- `mypy sakthai`: run strict type checking on the core package.
- `bandit -c pyproject.toml -r sakthai`: run the security scan.

## Coding Style & Naming Conventions

Target Python 3.11+ with strict typing. Follow the existing 100-character line length, use explicit imports, and keep edits small and surgical. Use `snake_case` for functions and variables, `PascalCase` for classes, and keep module names aligned to the seam they implement. Ruff handles linting and formatting.

## Testing Guidelines

Use `pytest` for all tests. Keep tests deterministic, network-free, and GCP-free unless they are explicitly marked as integration tests. Name files `test_*.py` and keep tests close to the behavior they cover. When changing behavior, add or update tests in `tests/` and run the relevant file plus the full suite when practical. CI gates `main` on lint, types, security, and pytest.

## Commit & Pull Request Guidelines

Commit messages should be short, imperative, and scoped when useful, such as `fix: tighten memory dedupe` or `docs: align agent guide`. Pull requests should explain the goal, summarize key changes, mention any affected subsystems, and include logs or screenshots when UI or runtime behavior changes. Link related issues when available.

## Security & Configuration Tips

Never commit secrets from `.env`, `.coverage`, or local tool directories. Keep auth and path changes routed through the existing seams: `MemoryStore` for SQLite, `agent/tools.py` and `agent/registry.py` for tool exposure, and `config.py` for paths. Respect the sandbox defaults (`read_file` is intentionally narrow; `run_command` is opt-in). If you touch deployment or agent-facing behavior, update `README.md`, `CLAUDE.md`, or `GEMINI.md`.
