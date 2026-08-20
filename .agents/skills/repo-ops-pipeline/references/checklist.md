# Pre-Release & Pull Request Checklist

Before submitting a Pull Request or pushing code to main, verify every item below:

## 1. Quality & Code Health
- [ ] `uv run ruff check .` is clean with zero warnings or errors.
- [ ] `uv run ruff format --check .` confirms correct formatting.
- [ ] `uv run mypy personas/sakthai/sakthai` passes in strict mode without errors.
- [ ] `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai` reports zero vulnerabilities.
- [ ] `uv run pytest tests/ -m "not integration"` passes completely.

## 2. Web Dashboard (`apps/sak_agent_dashboard`)
- [ ] `pnpm run typecheck` passes with no TypeScript errors.
- [ ] `pnpm run test` executes vitest specs cleanly.
- [ ] `pnpm run build` generates the production Next.js bundle without compilation errors.

## 3. Git Hygiene & PR Safety
- [ ] `git fetch origin` executed to pull latest remote references.
- [ ] Rebased onto `origin/main` to prevent merge conflicts.
- [ ] Checked `gh pr list` to confirm no duplicate or overlapping PRs exist for the same files.
- [ ] No credentials, `.env` files, or private keys are staged in git.
