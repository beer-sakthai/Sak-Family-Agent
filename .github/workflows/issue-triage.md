---
emoji: 🏷️
description: Triage newly opened issues by labeling type and priority, detecting duplicates, asking clarifying questions, and assigning owners.
intent: Automatically classify, deduplicate, clarify, and route newly opened repository issues.
on:
  issues:
    types: [opened]
  roles: all
permissions:
  contents: read
  issues: read
  pull-requests: read
tools:
  github:
    mode: gh-proxy
    toolsets: [default]
steps:
  - name: Pre-fetch existing issues for duplicate detection
    env:
      GH_TOKEN: ${{ github.token }}
      REPO: ${{ github.repository }}
    run: |
      mkdir -p /tmp/gh-aw/data
      gh issue list --repo "$REPO" --state all --limit 100 \
        --json number,title,state,labels,createdAt,url > /tmp/gh-aw/data/existing-issues.json
safe-outputs:
  add-labels:
    allowed:
      - bug
      - enhancement
      - documentation
      - question
      - invalid
      - duplicate
      - "priority: critical"
      - "priority: high"
      - "priority: medium"
      - "priority: low"
    target: "triggering"
  add-comment:
    max: 1
    target: "triggering"
  assign-to-user:
    allowed:
      - beer-sakthai
    max: 1
    target: "triggering"
  noop:
network:
  allowed: []
---

# Issue Triage

## Task

Objective: Automatically classify, deduplicate, clarify, and route the newly opened issue `#${{ github.event.issue.number }}` in `${{ github.repository }}`.

Determine applicability from the triggering issue context and `/tmp/gh-aw/data/existing-issues.json`. If the issue was already triaged or requires no action, call `noop` with a short reason and take no visible write action.

### 1. Inspect the Triggering Issue and Pre-fetched Data

1. Read the triggering issue details (`#${{ github.event.issue.number }}`) and compare its title and description against `/tmp/gh-aw/data/existing-issues.json` (excluding `#${{ github.event.issue.number }}` itself).
2. Check `.github/CODEOWNERS` and `AGENTS.md` to identify which subsystem and Sak Family persona own the area described in the issue:
   - **SakThai** (`@sakthai_agent_bot`) — Core orchestration, Hugging Face Hub, model routing, lead architecture (`personas/sakthai/`)
   - **SakSee** (`@saksee_agent_bot`) — Web, browser specialist, Next.js dashboard (`apps/sak_agent_dashboard/`, `personas/sakthai/sakthai/web/`)
   - **SakJules** (`@sakjules_agent_bot`) — GitHub Actions, CI/CD, security hardening, guardrails (`.github/workflows/`, `agent/guardrails*.py`)
   - **SakKing** (`@sakking_agent_bot`) — General assistant, CLI runner, client/team tools (`cli/`, `client/`, `team/`)
   - **SakSit** (`@saksit_agent_bot`) — Social and content workflows (`personas/saksit/`)
   - **SakTan** (`@saktan_agent_bot`) — Daily operations, cron schedules, local Ollama (`personas/saktan/`)

### 2. Classify Type and Priority Labels

Use `add-labels` to apply:
- **One type label**: `bug`, `enhancement`, `documentation`, `question`, or `invalid` (plus `duplicate` if a duplicate is identified).
- **One priority label**:
  - `priority: critical` — Security vulnerabilities, data loss, guardrails bypass, or broken production/main build.
  - `priority: high` — Core CLI, agent loop, memory store, or CI failure blocking development.
  - `priority: medium` — Standard bug or scoped feature enhancement.
  - `priority: low` — Minor documentation tweak, cosmetic UI polish, or general question.

### 3. Check for Duplicates

- If an existing issue in `/tmp/gh-aw/data/existing-issues.json` addresses the same root problem or feature request:
  - Include the `duplicate` label via `add-labels`.
  - In your triage comment (`add-comment`), link the original issue (`#N`) and note why it appears to be a duplicate, leaving the issue open for human verification.

### 4. Check Clarity and Ask Clarifying Questions

- If the issue description is missing essential details (for example: reproduction steps, command run, error traceback, affected persona, or expected behavior for a bug):
  - Include 1–3 concise, targeted clarifying questions in your `add-comment` response.

### 5. Assign and Route

- Use `assign-to-user` to assign `beer-sakthai` (the repository code owner in `.github/CODEOWNERS`).
- Post a single concise comment via `add-comment` summarizing:
  - Assigned type and priority classification
  - Relevant Sak Family persona lane (`SakThai`, `SakSee`, `SakJules`, `SakKing`, `SakSit`, or `SakTan`) and affected subsystem paths
  - Duplicate link (if any) and clarifying questions (if any)

## Safe Outputs

- Use `add-labels` to apply allowed type and priority labels to the triggering issue.
- Use `assign-to-user` to assign `beer-sakthai` to the triggering issue.
- Use `add-comment` (at most 1 comment) to post the triage summary, duplicate notice, or clarifying questions.
- Call `noop` with a short reason when no triage action is needed.
