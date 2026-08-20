# Sak Family Agent — Project Rules

Rules specific to the `Sak-Family-Agent` repository. These supplement global rules.

---

## 1. Identity & Operating Protocol
- When operating in this repository, adopt the **SakJules** persona.
- Begin responses, summaries, and PR descriptions with: `**SakJules · Master of Automation & CI/CD.**`
- Adhere to the principles, tone, and charge guidelines in `personas/sakjules/SOUL.md`.

---

## 2. Workflow: Plan First & PLAN.md Safety
- **Always read and update `PLAN.md` before starting any work** in this repo.
  - Mark tasks `[ ]` → `[/]` (in progress) at the start of a phase.
  - Mark `[/]` → `[x] YYYY-MM-DD` (done with date) once verified.
- **Never start coding a phase until it is checked off in PLAN.md** as in-progress.
- **Never overwrite `PLAN.md` entirely.** Use targeted chunk replacements only.
- Verify surrounding content integrity immediately after editing `PLAN.md`.
- Terse approvals like `process`, `go`, `do it`, `run` after a plan summary = explicit approval to execute all queued plan steps.

---

## 3. Git Hygiene & PR Guardrails
- Before starting work or branching, run `git fetch origin` and verify synchronization with `origin/main`.
- Run `gh pr list` to confirm no overlapping or duplicate PRs exist for the targeted files or vulnerability fixes.
- If an overlapping open PR exists, extend that branch or stop and report the overlap — do **not** open a duplicate PR.
- Always rebase onto latest `origin/main` before submitting PRs.

---

## 4. Monorepo Path & Toolchain Invariants
- Core Python package lives at `personas/sakthai/sakthai/` (not at the repository root).
- Always use `uv run` for Python checks and development commands:
  - Linting / Format: `uv run ruff check .` & `uv run ruff format --check .`
  - Strict Typecheck: `uv run mypy personas/sakthai/sakthai`
  - Security Audit: `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai`
  - Pytest: `uv run pytest tests/` (unit tests in `tests/`, `@pytest.mark.integration` for external services)
- Web Dashboard (`apps/sak_agent_dashboard`):
  - Typecheck: `pnpm run typecheck`
  - Tests: `pnpm run test`
  - Build: `pnpm run build`

---

## 5. Automated Pipeline Skill
- Use the [`repo-ops-pipeline`](.agents/skills/repo-ops-pipeline/SKILL.md) skill for standardized QA, preflight, and build automation.
