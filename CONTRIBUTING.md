# Contributing to sakthai-agent (v2)

Thanks for your interest in `sakthai-agent`. This document explains how the
project is organized, how to set up a development environment, and the bar that
changes must clear before they land on `main`.

## A note on licensing

This repository is the active, clean from-scratch rewrite of the core engine,
and is currently maintained as a **personal project**. As noted in the
[README](README.md), the source is provided for reading and learning. External
pull requests are not actively solicited, but if you have access to contribute,
the workflow and quality bar below apply to every change.

## Project layout

```
sakthai/     the package (memory, agent, mcp, cycle, skills, dashboard, cli)
tests/       unit tests (hermetic — no network, no GCP)
skills/      top-level skills (sakthai-personal, sakthai-cycle-*)
library/     curated library of SakThai's own skills, grouped by category
docs/        architecture and capabilities docs
scripts/     bootstrap.sh, setup-extensions.sh
data/        memory snapshot format + a sample export
```

See [`docs/architecture.md`](docs/architecture.md) for the full data-flow
diagram and [`CLAUDE.md`](CLAUDE.md) for the architectural ground rules.

## Development setup

Python **>= 3.11** is required (CI runs on 3.11 and 3.12).

```bash
cp .env.example .env          # then fill in ANTHROPIC_API_KEY
pip install -e ".[dev]"       # editable install with the dev toolchain
pip install -e ".[dashboard]" # optional: streamlit/plotly/pandas for the dashboard
pip install -e ".[cloud]"     # optional: google-adk/aiplatform for `sakthai cloud`
pip install -e ".[all]"       # dev + dashboard + cloud
```

Verify your environment with `sakthai doctor` and `sakthai setup`.

## The quality bar

CI runs a fixed sequence on every pull request, and **green CI is the bar for
`main`.** Run the same checks locally before pushing:

```bash
ruff check sakthai tests          # lint
ruff format --check sakthai tests # format check (drop --check to apply)
mypy sakthai                      # strict type-check
bandit -c pyproject.toml -r sakthai  # security scan
python -m pytest tests/ -q        # full unit suite
```

To run a single test file:

```bash
python -m pytest tests/test_memory_store.py -q
```

Notes:

- **`mypy` is `strict`** over `sakthai/` (the Streamlit `dashboard/app.py` is the
  one loosened module). Keep new code strict-clean.
- **`ruff` excludes `library/` and `scripts/`,** and `mypy` only covers
  `sakthai/`. Don't "fix" lint or types in those trees.
- **Tests must stay hermetic** — no network calls and no GCP credentials. Inject
  clients and stores rather than reaching out.
- A **secret scan** (gitleaks) runs first in CI. Never commit secrets; `.env` is
  gitignored and only `.env.example` is committed.

## Architectural ground rules

These conventions keep the package small and strictly layered. Please respect
them:

- **The memory store is the seam.** Anything that touches SQLite goes through
  `MemoryStore` (`sakthai/memory/store.py`). Schema changes are additive
  migrations in `_migrate_schema()` (`ALTER TABLE` only, under
  `BEGIN IMMEDIATE`).
- **Tools are defined once.** Add a tool to `BUILTIN_TOOLS` in
  `sakthai/agent/tools.py` and it appears in both the agent loop and the MCP
  server via `agent/registry.py`. Don't bypass the registry.
- **Paths live in `config.py`.** Nothing else hard-codes a path; new paths go
  there.
- **Auth goes through `auth.py`.** Call `resolve_anthropic_client()` (and the
  matching resolvers) rather than constructing a client directly.
- **Sandbox defaults are deliberate.** `read_file` is restricted to cwd +
  `~/.sakthai` + `SAKTHAI_READ_ALLOW`; `run_command` is opt-in via
  `SAKTHAI_SHELL_ALLOW`. Don't widen these without a clear reason.

The original `SakThai-Agent` (v1) is a read-only blueprint: consult it for
intent, but never copy its code or layout into this repo — re-derive everything.

## Commit and pull-request guidelines

- Write clear, descriptive commit messages explaining the *why*, not just the
  *what*.
- Keep each change focused; prefer small, reviewable PRs.
- Make sure the full local check sequence above passes before you open a PR.
- Update relevant docs (`README.md`, `docs/`, `CLAUDE.md`) when behavior or
  conventions change.

## Reporting security issues

Please do **not** open public issues for security vulnerabilities. Follow the
process in [`SECURITY.md`](SECURITY.md) instead.
