---
emoji: 🛠️
description: Regularly inspect the repository for bounded maintenance work, validate one improvement, and open a small draft pull request.
intent: Select one low-risk, high-value maintenance improvement, validate it with the repository quality suite, and open a draft pull request.
on:
  schedule: daily
  workflow_dispatch:
  skip-if-match: 'is:pr is:open in:title "[maintainer] "'
permissions:
  contents: read
  issues: read
  pull-requests: read
tools:
  github:
    mode: gh-proxy
    toolsets: [default]
steps:
  - name: Pre-fetch repository maintenance signals
    env:
      GH_TOKEN: ${{ github.token }}
      REPO: ${{ github.repository }}
    run: |
      mkdir -p /tmp/gh-aw/data
      gh issue list --repo "$REPO" --state open --limit 50 \
        --json number,title,labels,createdAt,url > /tmp/gh-aw/data/open-issues.json
      gh pr list --repo "$REPO" --state open --limit 30 \
        --json number,title,author,labels,isDraft,createdAt,url > /tmp/gh-aw/data/open-prs.json
      git log -n 30 --oneline > /tmp/gh-aw/data/recent-commits.txt
safe-outputs:
  create-pull-request:
    title-prefix: "[maintainer] "
    labels:
      - agentic-workflows
    reviewers:
      - beer-sakthai
    draft: true
    expires: 7
    allowed-files:
      - "personas/sakthai/**/*.py"
      - "tests/**/*.py"
      - "scripts/**/*.py"
      - "apps/sak_agent_dashboard/src/**/*.ts"
      - "apps/sak_agent_dashboard/src/**/*.tsx"
      - "docs/**/*.md"
    excluded-files:
      - "**/guardrails*.py"
      - "**/security_hardening.py"
      - "**/web/server.py"
      - "**/SOUL.md"
      - "AGENTS.md"
      - ".agents/AGENTS.md"
      - "CLAUDE.md"
      - "GEMINI.md"
      - "PLAN.md"
      - "**/*.lock"
  noop:
network:
  allowed:
    - defaults
    - python
    - node
---

# Repository Maintainer

## Task

Objective: Act as a conservative repository maintainer for `${{ github.repository }}` — inspect `/tmp/gh-aw/data/` signals and the codebase, select **one** bounded, low-risk improvement, verify it with the repository's test/quality suite, and open a small draft pull request.

### 1. Read Repository Guidelines and Signals

1. Read `AGENTS.md` and `/tmp/gh-aw/data/open-prs.json` first. Never duplicate work already covered by an open pull request.
2. Inspect `/tmp/gh-aw/data/open-issues.json` and `/tmp/gh-aw/data/recent-commits.txt` to understand recent changes and open maintenance candidates.
3. Never modify protected or multi-persona parity files (`**/guardrails*.py`, `**/security_hardening.py`, `**/web/server.py`, `**/SOUL.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PLAN.md`, or lockfiles).

### 2. Select Exactly One Bounded Task

Choose one small, self-contained task from this priority order:
1. **Actionable low-risk bug or test gap from an open issue** (when clearly reproducible and fixable within allowed files).
2. **Unit test & branch-coverage hardening** in `tests/` for uncovered branches or error paths in `personas/sakthai/`.
3. **Static type, lint, or dead-code cleanup** in `personas/sakthai/`, `scripts/`, or `apps/sak_agent_dashboard/src/`.
4. **Documentation accuracy fix** in `docs/**/*.md` where a code path or CLI flag is documented inaccurately.

Keep the diff focused on a single concern (ideally 1–3 files). Preserve public APIs and do not add new dependencies.

### 3. Validate Before Opening a Draft Pull Request

Run the applicable quality checks and ensure all pass before creating the PR:
- For Python changes (`personas/sakthai/`, `tests/`, `scripts/`):
  - `uv run ruff check <changed-files>`
  - `uv run mypy personas/sakthai`
  - `uv run bandit -c pyproject.toml -r personas/sakthai`
  - `uv run pytest tests/ -q`
- For Next.js dashboard changes (`apps/sak_agent_dashboard/`):
  - `npm --prefix apps/sak_agent_dashboard test -- --run`
  - `npm --prefix apps/sak_agent_dashboard run lint`

If validation fails and the root cause cannot be cleanly resolved within scope, revert your changes and call `noop` explaining what failed.

### 4. Open Draft Pull Request

When the change is verified and all checks are green, call `create-pull-request` with:
- A clear title (`[maintainer] <concise summary>`)
- **What and why**: 1 short paragraph explaining the maintenance improvement and its motivation
- **Validation**: exact commands run and their results

## Safe Outputs

- Use `create-pull-request` to open a single small draft pull request with the validated improvement.
- Call `noop` with a short explanation when no safe, bounded maintenance task is found or if validation cannot pass cleanly.
