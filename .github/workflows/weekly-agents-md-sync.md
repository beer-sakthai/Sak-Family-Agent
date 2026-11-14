---
emoji: 🤖
description: Weekly workflow that reviews merged pull requests and updated source files to keep root AGENTS.md accurate and current.
intent: Maintain root AGENTS.md accuracy against merged pull requests and repository structure changes via a weekly review-gated pull request.
on:
  schedule: weekly
  workflow_dispatch:
  skip-if-match: 'is:pr is:open in:title "[agents-md-sync] "'
permissions:
  contents: read
  issues: read
  pull-requests: read
tools:
  github:
    mode: gh-proxy
    toolsets: [default]
steps:
  - name: Pre-fetch weekly merged PRs and source tree changes
    env:
      GH_TOKEN: ${{ github.token }}
      REPO: ${{ github.repository }}
    run: |
      mkdir -p /tmp/gh-aw/data
      WINDOW_START=$(date -u -d '7 days ago' '+%Y-%m-%dT%H:%M:%SZ')
      gh pr list --repo "$REPO" --state merged --limit 100 \
        --json number,title,mergedAt,files,url \
        | jq --arg since "$WINDOW_START" '[.[] | select(.mergedAt >= $since)]' > /tmp/gh-aw/data/weekly-merged-prs.json
      git log --since="7 days ago" --name-status --pretty=format:"COMMIT:%H %s" > /tmp/gh-aw/data/weekly-git-log.txt || true
safe-outputs:
  create-pull-request:
    title-prefix: "[agents-md-sync] "
    labels:
      - documentation
      - agentic-workflows
    reviewers:
      - beer-sakthai
    draft: false
    expires: 7
    allowed-files:
      - "AGENTS.md"
    protected-files: request-review
  noop:
network:
  allowed: []
---

# Weekly AGENTS.md Maintenance

## Task

Objective: Review pull requests merged and source files updated over the past 7 days (or since the last update to `AGENTS.md`) and open a pull request if root `AGENTS.md` is out of sync with the repository.

### 1. Inspect Recent Changes and Current `AGENTS.md`

1. Read `/tmp/gh-aw/data/weekly-merged-prs.json` and `/tmp/gh-aw/data/weekly-git-log.txt`.
2. Read the current root `AGENTS.md` and verify every factual claim against the live repository:
   - **Project Structure & Module Organization**: subpackages under `personas/sakthai/`, `tests/`, `docs/`, `personas/<name>/`, `scripts/`, and `infra/`.
   - **Build, Test, and Development Commands**: `Makefile` targets, `pyproject.toml` scripts/extras, `uv` commands, and path-resolution notes.
   - **Coding Style & Naming Conventions**: Python version floor, Ruff line-length and formatting rules in `pyproject.toml`.
   - **Testing Guidelines**: Pytest markers, coverage floor (`--cov-fail-under` in `.github/workflows/ci.yml` and `pyproject.toml`).
   - **Agent-Specific Instructions**: Preserve the SakJules persona rules, `SOUL.md` reference, and No-Duplicate-PRs policy intact unless an explicit merged PR changed those rules.

### 2. Update `AGENTS.md` Only When Evidence Supports It

- If all claims in `AGENTS.md` match the repository state, call `noop` with a brief explanation and make no file changes.
- If any subpackage list, command, coverage floor, or convention in `AGENTS.md` is outdated relative to merged code changes:
  - Make a surgical edit to `AGENTS.md` preserving all unchanged sections and rules.
  - Call `create-pull-request` summarizing each factual correction and citing the merged PR or file where the change occurred.

## Safe Outputs

- Use `create-pull-request` (restricted to `AGENTS.md` with `protected-files: request-review`) to propose updates when drift is confirmed.
- Call `noop` with a short explanation when `AGENTS.md` is already accurate and current.
