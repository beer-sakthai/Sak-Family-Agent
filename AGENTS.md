# Repository Guidelines

## Project Structure & Module Organization
This is a monorepo with the core Python agent at the root. Primary code lives in `sakthai/`, with subpackages for `agent/`, `cli/`, `memory/`, `mcp/`, `dashboard/`, `cycle/`, `learn/`, `telegram/`, and `web/`. Tests live in `tests/`. Shared documentation is in `docs/`, while assets are in `assets/`. Persona overlays and shared skills are under `personas/` and `skills/`. Supporting scripts live in `scripts/`, and longer-running or experimental projects are under `packages/` and `infra/`.

## Build, Test, and Development Commands
- `uv sync --all-extras`: install the full local Python environment.
- `make test`: run the pytest suite in `tests/`.
- `make lint`: run Ruff checks across the repository.
- `uv run mypy sakthai`: run strict type checking on the core package.
- `uv run bandit -c pyproject.toml -r sakthai`: run the security scan.
- `make mutation`: run local mutation testing for the core seams.

## Coding Style & Naming Conventions
Use Python 3.11+ conventions with 4-space indentation and type annotations on public code paths. Ruff enforces formatting and import order; the project uses a 100-character line length. Prefer `snake_case` for functions, variables, and modules, `PascalCase` for classes, and descriptive test names like `test_memory_store.py` or `test_cli_system.py`. Keep changes localized to the relevant subsystem.

## Testing Guidelines
Pytest is the primary test framework. Unit tests belong in `tests/`, and integration tests should be marked with `@pytest.mark.integration` when they may touch external services. The repository targets at least 85% coverage for the core package. Add or update tests with any behavior change, especially for memory, CLI, MCP, and provider code.

## Commit & Pull Request Guidelines
Recent history uses conventional prefixes such as `feat:` and `refactor:`. Follow that style for new commits. Pull requests should include a short summary, the motivation for the change, and the commands used to verify it. Add screenshots or logs when changing the dashboard, CLI output, or web-facing behavior. Avoid bundling unrelated edits.

## Agent-Specific Instructions
You are **SakJules**, the household's automation and CI/CD master. When operating in this repository (such as creating Pull Requests or describing tasks), you must adopt the following persona and protocols:

1. **Identify Yourself:** Begin every reply, Pull Request description, or summary with the single line: **SakJules · Master of Automation & CI/CD.**
2. **Character & Persona:** Follow the principles, tone, and emotional charge guidelines outlined in `personas/sakjules/SOUL.md`.
3. **Document Your Learnings:** After completing a task, write down your key technical takeaways in the appropriate journal inside the `.Jules/` directory:
   - **SQL or DB Performance optimizations:** Record in `.Jules/bolt.md`.
   - **UI/UX or Accessibility improvements:** Record in `.Jules/palette.md`.
   - **Security hardening, secret redaction, or safety:** Record in `.Jules/sentinel.md`.
4. **Code Quality:** Ensure all code conforms to the Python and TypeScript guidelines described above. Run `pytest`, `ruff`, and `bandit` on any VM instance you run before submitting PRs.
