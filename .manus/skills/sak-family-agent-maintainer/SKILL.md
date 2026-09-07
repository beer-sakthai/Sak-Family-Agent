---
name: sak-family-agent-maintainer
description: "Maintain, test, document, and safely integrate changes in the beer-sakthai/Sak-Family-Agent repository. Use for repository tasks involving the SakThai runtime, personas, dashboard, tests, CI, security workflows, README/status updates, branch consolidation, commits, pull requests, or releases."
---

# Sak-Family-Agent Maintainer

Maintain `beer-sakthai/Sak-Family-Agent` as a multi-surface Python and TypeScript repository. Follow the repository’s own plans and agent guidance before editing, preserve one source of truth per topic, and prefer small, reviewable changes.

## Start every task

1. Work from the repository root and inspect the current branch, worktree, remotes, and recent history.
2. Read `AGENTS.md`, `CLAUDE.md`, `PLAN.md`, and the nearest component documentation before changing code.
3. Classify the change: core Python runtime, persona/skill content, dashboard, training, infrastructure, documentation, or CI/security.
4. Identify canonical test and lint commands from `Makefile`, `pyproject.toml`, the component `package.json`, and `.github/workflows/` rather than guessing.
5. Make a short task plan for multi-step work. Do not mix unrelated cleanup into the change.

## Repository map

- `personas/sakthai/sakthai/`: installed provider-agnostic agent runtime, CLI, memory, MCP, web API, guardrails, and tools.
- `personas/*/`: persona overlays, configuration, skills, and self-evolution material.
- `personas/shared/` and `library/`: shared skills and curated reusable knowledge.
- `tests/`: Python tests for the core runtime and supporting systems.
- `apps/sak_agent_dashboard/`: Next/Vitest dashboard application with its own npm lockfile and scripts.
- `training/`, `services/`, and `infra/`: model training, serving, deployment, and operational assets.
- `docs/`: architecture, audits, plans, security notes, and operational documentation.
- `.github/workflows/`: CI, security, dependency, evaluation, and maintenance automation.

For detailed commands and gate mapping, read [repository-map.md](references/repository-map.md). For integration and verification rules, read [verification-and-integration.md](references/verification-and-integration.md).

## Editing rules

- Prefer surgical edits. Preserve surrounding naming, formatting, and documentation style.
- Keep safety controls intact. Treat shell execution, filesystem access, network requests, credentials, MCP servers, Telegram, email, and calendar integrations as security-sensitive.
- Do not weaken guardrails, secret scanning, path validation, authentication, sandboxing, or CI thresholds to make a task pass.
- Update tests when behavior changes. Add regression coverage for security and boundary conditions.
- Update the closest canonical documentation when interfaces, commands, configuration, or operational behavior changes.
- Do not copy repository facts into multiple documents; link to the authoritative file instead.

## Verification workflow

1. Inspect the diff with `git diff` and run `git diff --check`.
2. For core Python changes, run the relevant focused tests first, then the repository gates: `make lint`, strict mypy, Bandit, and pytest. Respect the CI coverage floor of 96% when the change affects measured code.
3. For dashboard changes, run commands from `apps/sak_agent_dashboard/package.json`, normally `npm test`, `npm run lint`, and `npm run build`. Use the repository’s configured package manager and report engine or environment limitations instead of hiding them.
4. For documentation-only changes, validate Markdown structure, links, code fences, and factual counts. Do not claim a live status from an old local snapshot; distinguish recorded verification from live workflow badges.
5. Compare failures with a clean baseline when practical. Existing failures are not regressions, but new failures introduced by the change block integration until resolved or explicitly accepted by the user.

## Git and GitHub workflow

- Keep the user’s requested target branch explicit. For this repository, `main` is the protected integration branch.
- Never bypass branch protection or required checks. If direct pushes to `main` are rejected, create a descriptive branch, push it, open a pull request, wait for required checks, and merge through the pull request.
- Use `gh` for GitHub operations and inspect pull-request status before merging.
- Use clear conventional commit messages such as `feat(scope): ...`, `fix(scope): ...`, or `docs: ...`.
- Before reporting completion, verify the merged commit on `origin/main`, the worktree is clean, and remote branches match the user’s requested consolidation state.
- Delete temporary branches only after their changes are merged and no longer needed. Never delete an unmerged branch without explicit user approval.

## Communication and completion

Report what changed, which validations passed or failed, the exact commit or pull request, and any remaining caveats. For status dashboards and repository metrics, include the measurement date and commands used. Never present a local snapshot as live CI state.
