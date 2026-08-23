# ci-cd-doctor

CI/CD failure triage skill for the Sak-Family-Agent workspace.

## Skills

- **ci-cd-doctor** — Systematic diagnosis and remediation guide for GitHub Actions CI/CD failures, CodeQL security findings, and multi-package monorepo test gates. Use when `gh pr checks <id>` shows red, ESLint/CodeQL annotations block a PR, or subproject `pytest`/`ruff` gates fail. Honors this repo's non-author-approval merge policy: fixes are committed locally by default (no auto-push, no auto-PR).

## Install (local, from this repo)

```bash
claude plugin add ./path/to/Sak-Family-Agent/.claude-plugins/ci-cd-doctor
```

Then enable it:

```bash
claude plugin enable ci-cd-doctor@local
```

Restart Claude Code and the `ci-cd-doctor` skill will be auto-activated when the task context matches its description.

## Per-project configuration

Create `.claude/ci-cd-doctor.local.md` (YAML frontmatter, gitignored — never committed) to override defaults:

```yaml
---
enabled: true                                  # master toggle; false = skip this skill entirely
auto_push: false                              # false (default) = commit locally, do NOT push or open a PR
verification_suites: ["dashboard", "python"]   # which verification blocks to run
---
```

Absent file → use the defaults above. Parsing uses `grep`/`sed` (`jq` is not installed in this repo). See the skill's `## Configuration` section for the full contract.

## Scope

Tailored to this codebase's real CI surfaces:

- **Dashboard gate** — `apps/sak_agent_dashboard` (`pnpm lint` → `typecheck` → `test` → `build`; `eslint-config-next` v16 enables the React-Compiler rules that catch what a green vitest run misses).
- **Python gate** — `personas/sakthai/sakthai` + `tests/` (ruff → mypy → bandit → pytest, 96% coverage floor).
- **Workflow invariants** — CodeQL advanced setup (`.github/codeql/codeql-config.yml`) and `tests/test_workflow_hygiene.py` (every workflow loadable, SHA-pinned, top-level `permissions:`).
- The self-healing CI agent (`sakthai heal`) is a related but separate automated pipeline — this skill triages what `heal` would act on.

## Two surfaces (keep in sync)

The same skill also lives at `.agents/skills/ci-cd-doctor/SKILL.md` for the acli/agents-CLI runtime. The two copies are intentionally byte-identical; if you edit one, update the other. Both read the same `.claude/ci-cd-doctor.local.md` settings file.
