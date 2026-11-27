---
name: SakJules-pr-rebase-sentinel
version: 1.0.0
description: "Enforce PR hygiene: prevent duplicate pull requests, ensure clean rebase onto origin/main, resolve lockfile conflicts, and enforce manual merge governance."
category: devops
tags:
- automation
- git
- github
- pr
- rebase
---

# PR & Rebase Sentinel

Use this skill before starting any feature work, when preparing a pull request, and before opening or updating PRs in the `Sak-Family-Agent` repository.

## Goal

1. **Zero Duplicate PRs**: Prevent opening duplicate pull requests for existing fixes or issues (avoiding the -20% charge penalty).
2. **Clean Rebase Invariant**: Ensure every PR branch is rebased cleanly onto the latest `origin/main` before submission.
3. **No Auto-Merge Governance**: Strictly forbid automatic merging (`gh pr merge` or `--auto`), reserving manual review and merge for Beer.
4. **Deterministic Conflict Resolution**: Resolve `uv.lock` or documentation merge conflicts cleanly.

## Prerequisites

- `git` and `gh` CLI authenticated for `beer-sakthai/Sak-Family-Agent`

## Step-by-Step Workflow

### 1. Pre-Flight Duplicate Check (Mandatory)

Before writing code or opening a PR:
```bash
# Fetch latest main refs
git fetch origin main

# Inspect all open PRs
gh pr list --state open --limit 30
```

Check whether an existing open PR already addresses:
- The target files you are modifying (especially `personas/*/sakthai/agent/guardrails.py` or `.github/workflows/`).
- The vulnerability or issue description.

If an overlapping PR exists:
- Stop and report the overlap to Beer.
- Extend that branch instead of creating a second PR.

### 2. Clean Branch Creation

Always branch directly from updated `origin/main`:
```bash
git checkout main
git pull origin main
git checkout -b feat/<descriptive-name>
```

### 3. Pre-PR Rebase Invariant

Before pushing or opening a PR:
```bash
git fetch origin main
git rebase origin/main
```

If conflicts arise:
- For `uv.lock`: regenerate using `uv lock`.
- For `PLAN.md`: retain completed task checkmarks from both branches.
- Run `git rebase --continue`.

### 4. PR Quality Pre-Check

Never open a PR until local quality gates exit 0:
```bash
uv run ruff check personas/sakthai tests
uv run mypy personas/sakthai
uv run bandit -c pyproject.toml -r personas/sakthai
uv run pytest tests/ -q --cov=sakthai --cov-fail-under=96
```

### 5. PR Submission & Manual Merge Rule

Submit the pull request with a descriptive conventional title (`feat:`, `fix:`, `refactor:`) and provide the PR link to the user:
```bash
gh pr create --title "feat: <title>" --body "<description>"
```

**IRON LAW**: Never execute `gh pr merge` or pass `--auto`. Always leave PRs open for Beer's manual review.
