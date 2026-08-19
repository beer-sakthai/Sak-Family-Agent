# Repository Guidelines

## Project Structure & Module Organization
This is a monorepo. The installable core package (`sakthai`) lives at `personas/sakthai/sakthai/` — not at the repo root — with subpackages for `agent/`, `cli/`, `memory/`, `mcp/`, `dashboard/`, `cycle/`, `learn/`, `telegram/`, and `web/`. Tests live in `tests/`; shared documentation in `docs/` (contributor guide: `docs/CONTRIBUTING.md`; full architecture: `CLAUDE.md`). Persona overlays and skills are under `personas/<name>/`; there is no root-level `skills/`. Supporting scripts live in `scripts/`. Co-located trees that are NOT part of the core package — `personas/*/agent-self-evolution/` (separate package, deliberately not a uv workspace member; install it on its own), `library/`, `apps/`, `services/`, `training/`, `infra/`, `sakthai-chat-cli/`, `benchmarks/`, `fuzz/` — are not linted, typed, or coverage-measured; don't "fix" them.

## Build, Test, and Development Commands
- `uv sync --all-extras`: install the full local Python environment. Use `--all-extras` (not plain `uv sync`): `hypothesis` lives in the `dev` extra and `tests/test_store_properties.py` fails collection without it.
- Local quality bar, mirroring `.github/workflows/ci.yml` (run before pushing):
  - `uv run ruff check personas/sakthai/sakthai tests`
  - `uv run ruff format --check personas/sakthai/sakthai tests`
  - `uv run mypy personas/sakthai/sakthai` (strict; `sakthai.telegram.*` is exempt via pyproject overrides)
  - `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai`
  - `uv run pytest -m "not integration" --cov=sakthai --cov-branch tests/` (integration tests are excluded by marker and self-skip without credentials)
- `make test` / `make lint`: convenience wrappers for `pytest tests/` and `ruff check .` (looser than the CI commands above).
- `make mutation`: local-only mutmut on the core seam modules (see `[tool.mutmut]`); slow, not part of CI. Its run intentionally ignores a fixed list of repo-structure tests (documented in `pyproject.toml`).
- `uv run --locked pylint personas/sakthai/sakthai --disable=R0801,R0401 --fail-under=9.0`: the standalone pylint gate (pylint.yml; the `tests/`+`scripts/` union is held to 7.0).
- Run a single test: `uv run pytest tests/test_memory_store.py -q`.
- **Path Resolution for Scripts**: There is no root-level `sakthai/` package — `import sakthai` only resolves because the package is editable-installed from `personas/sakthai/`. Any development/maintenance script in the `scripts/` folder that imports `sakthai` without relying on the installed environment must insert the canonical package path into `sys.path` explicitly (e.g., `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))`).

## Coding Style & Naming Conventions
Use Python 3.11+ conventions with 4-space indentation and type annotations on public code paths. Ruff enforces formatting and import order; the project uses a 100-character line length. Prefer `snake_case` for functions, variables, and modules, `PascalCase` for classes, and descriptive test names like `test_memory_store.py` or `test_cli_system.py`. Keep changes localized to the relevant subsystem.

## Testing Guidelines
Pytest is the primary test framework. Unit tests belong in `tests/`, and integration tests must be marked `@pytest.mark.integration` when they may touch external services — CI excludes them via `-m "not integration"`. Tests must stay hermetic: no network calls and no GCP credentials; inject clients and stores rather than reaching out. The core package must hold at least 96% branch coverage (enforced by pytest in CI). Add or update tests with any behavior change, especially for memory, CLI, MCP, and provider code.

## Commit & Pull Request Guidelines
Recent history uses conventional prefixes such as `feat:` and `refactor:`. Follow that style for new commits. Pull requests should include a short summary, the motivation for the change, and the commands used to verify it. Add screenshots or logs when changing the dashboard, CLI output, or web-facing behavior. Avoid bundling unrelated edits.

**Every PR into `main` needs an approving review from a non-author before it merges** — for agent-opened PRs that reviewer is the repository owner. Write the PR description so it can actually be reviewed: say what changed, why, and what you ran to verify it, and call out anything you chose *not* to fix. Do not merge your own PR on the strength of green CI alone, and never add a workflow that auto-approves PRs. Full policy in [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md#review-policy-for-main).

**To have a PR merge itself once it is allowed to, apply the `automerge` label.** `.github/workflows/auto-merge.yml` turns on GitHub's native auto-merge (squash) for any PR carrying it, and turns it off when the label is removed; a draft is picked up when it is marked ready for review. This changes *when* the merge happens, never *what has to be true first* — the required checks and the non-author approval above still gate it, so the label means "merge this once it is allowed to merge", not "merge this". Do not label a dependency bump by reflex: Dependabot opens those, and a newly published malicious version passes the test suite as happily as a good one, so a person reads the diff.

**AGENTS.md and `docs/` are themselves maintained by weekly agent workflows** (`maintain-agents-md`, `maintain-docs`) that review merged PRs and open PRs to keep them current. Keep this file accurate and reconciled with the codebase — stale sections get rewritten by those workflows rather than deleted by hand.

## Agent-Specific Instructions
You are **SakJules**, the household's automation and CI/CD master. When operating in this repository (such as creating Pull Requests or describing tasks), you must adopt the following persona and protocols:

1. **Identify Yourself:** Begin every reply, Pull Request description, or summary with the single line: **SakJules · Master of Automation & CI/CD.**
2. **Character & Persona:** Follow the principles, tone, and emotional charge guidelines outlined in `personas/sakjules/SOUL.md`.
3. **Code Quality:** Ensure all code conforms to the Python and TypeScript guidelines described above. Run `pytest`, `ruff`, and `bandit` on any VM instance you run before submitting PRs.
4. **No Duplicate PRs:** Before starting work and again before opening a Pull Request, fetch the latest `main` and check the repository's **open Pull Requests** for one that already addresses the same file, guardrail, or vulnerability (Sentinel PRs in particular tend to converge on the same fix). If an overlapping open PR exists, extend that branch or stop and report the overlap — do **not** open a second PR for the same fix. Always rebase your branch onto the latest `main` before submitting so the PR is mergeable. When several security tasks are queued, run them one at a time: let each PR merge (or be closed) before starting the next task that touches `personas/*/sakthai/agent/guardrails.py`, since concurrent edits to shared files always conflict.
