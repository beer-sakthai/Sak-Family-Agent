---
emoji: 📚
description: Daily check that identifies documentation files out of sync with recent code changes and opens a pull request with updates.
intent: Keep repository documentation under docs/ and README.md synchronized with recent code changes via a daily pull request.
on:
  schedule: daily
  workflow_dispatch:
  skip-if-match: 'is:pr is:open in:title "[doc-sync] "'
permissions:
  contents: read
  issues: read
  pull-requests: read
tools:
  github:
    mode: gh-proxy
    toolsets: [default]
steps:
  - name: Pre-fetch recent commits and changed files
    env:
      GH_TOKEN: ${{ github.token }}
      REPO: ${{ github.repository }}
    run: |
      mkdir -p /tmp/gh-aw/data
      git log --since="24 hours ago" --pretty=format:'{"sha":"%H","subject":%f,"date":"%cI"}' > /tmp/gh-aw/data/recent-commits.jsonl || true
      git log --since="24 hours ago" --name-only --pretty=format: | sort -u | sed '/^$/d' > /tmp/gh-aw/data/changed-files.txt || true
      gh pr list --repo "$REPO" --state merged --limit 30 \
        --json number,title,mergedAt,files,url > /tmp/gh-aw/data/recent-merged-prs.json
safe-outputs:
  create-pull-request:
    title-prefix: "[doc-sync] "
    labels:
      - documentation
      - agentic-workflows
    reviewers:
      - beer-sakthai
    draft: false
    expires: 7
    allowed-files:
      - "docs/**/*.md"
      - "README.md"
    excluded-files:
      - "**/SOUL.md"
      - "AGENTS.md"
      - ".agents/AGENTS.md"
      - "CLAUDE.md"
      - "GEMINI.md"
      - "PLAN.md"
  noop:
network:
  allowed: []
---

# Daily Documentation Sync

## Task

Objective: Inspect code changes merged over the last 24 hours (or since the last documentation update) and update out-of-sync documentation files under `docs/**/*.md` and `README.md`.

### 1. Inspect Recent Code Changes

1. Read `/tmp/gh-aw/data/changed-files.txt`, `/tmp/gh-aw/data/recent-commits.jsonl`, and `/tmp/gh-aw/data/recent-merged-prs.json`.
2. If no source files (`personas/sakthai/sakthai/**`, `apps/**`, `scripts/**`, `.github/workflows/**`, `pyproject.toml`) changed in the window, or if all documentation already reflects current behavior, call `noop` with a brief explanation and make no edits.

### 2. Verify Documentation Accuracy Against Code

Compare changed code paths against the relevant documentation files:
- CLI subcommands and options (`personas/sakthai/sakthai/cli/`) → `README.md`, `docs/SAKTHAI.md`, `docs/capabilities.md`
- Built-in agent tools and architecture (`personas/sakthai/sakthai/agent/`, `personas/sakthai/sakthai/mcp/`) → `docs/architecture.md`, `docs/capabilities.md`, `README.md`
- Web API and dashboard (`personas/sakthai/sakthai/web/`, `apps/sak_agent_dashboard/`) → `docs/architecture.md`, `README.md`
- Security guardrails (`personas/sakthai/sakthai/agent/guardrails.py`) → `docs/security-hardening.md`, `README.md`

### 3. Apply Surgical Updates and Open a Pull Request

- Edit only `docs/**/*.md` and `README.md` where factual drift is verified in code.
- Never modify `SOUL.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or `PLAN.md`.
- Preserve existing formatting, diagrams, and prose that remain accurate.
- When updates are made, call `create-pull-request` with a concise summary listing each updated doc file and the exact code change or commit that motivated it.

## Safe Outputs

- Use `create-pull-request` to open a pull request containing only updates to `docs/**/*.md` and `README.md`.
- Call `noop` with a short explanation when no documentation files are out of sync.
