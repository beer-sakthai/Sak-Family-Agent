---
emoji: 📊
description: Generate a daily issue report summarizing new issues, merged pull requests, and open blockers over the last 24 hours.
intent: Provide a daily repository activity digest of new issues, merged pull requests, and active blockers delivered as a GitHub issue.
on:
  schedule: daily
  workflow_dispatch:
permissions:
  contents: read
  issues: read
  pull-requests: read
tools:
  github:
    mode: gh-proxy
    toolsets: [default]
steps:
  - name: Pre-fetch repository activity for the last 24 hours
    env:
      GH_TOKEN: ${{ github.token }}
      REPO: ${{ github.repository }}
    run: |
      mkdir -p /tmp/gh-aw/data
      WINDOW_START=$(date -u -d '24 hours ago' '+%Y-%m-%dT%H:%M:%SZ')
      WINDOW_END=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
      jq -n --arg start "$WINDOW_START" --arg end "$WINDOW_END" \
        '{window_start_utc: $start, window_end_utc: $end}' > /tmp/gh-aw/data/window.json
      gh issue list --repo "$REPO" --state all --limit 100 \
        --json number,title,state,author,labels,createdAt,closedAt,url \
        | jq --arg since "$WINDOW_START" '[.[] | select(.createdAt >= $since)]' > /tmp/gh-aw/data/new-issues.json
      gh pr list --repo "$REPO" --state merged --limit 100 \
        --json number,title,author,labels,mergedAt,url \
        | jq --arg since "$WINDOW_START" '[.[] | select(.mergedAt >= $since)]' > /tmp/gh-aw/data/merged-prs.json
      gh issue list --repo "$REPO" --state open --limit 100 \
        --json number,title,author,labels,createdAt,url > /tmp/gh-aw/data/open-issues.json
      gh pr list --repo "$REPO" --state open --limit 50 \
        --json number,title,author,labels,isDraft,reviewDecision,statusCheckRollup,createdAt,url > /tmp/gh-aw/data/open-prs.json
safe-outputs:
  create-issue:
    title-prefix: "[daily-report] "
    labels:
      - report
      - daily-status
    close-older-issues: true
    close-older-key: "daily-activity-report"
    expires: 7
    max: 1
  noop:
network:
  allowed: []
---

# Daily Repository Activity Report

## Task

Objective: Summarize repository activity over the last 24 full hours ending at workflow start (UTC) — covering new issues, merged pull requests, and any open blockers — and publish the digest as a GitHub issue.

Read the pre-fetched data files in `/tmp/gh-aw/data/`:
- `/tmp/gh-aw/data/window.json` (`window_start_utc` and `window_end_utc`)
- `/tmp/gh-aw/data/new-issues.json` (issues opened during the 24-hour window, excluding prior `[daily-report]` issues)
- `/tmp/gh-aw/data/merged-prs.json` (pull requests merged during the 24-hour window)
- `/tmp/gh-aw/data/open-issues.json` and `/tmp/gh-aw/data/open-prs.json` (current open items to evaluate for blockers)

### 1. Identify Open Blockers

From `/tmp/gh-aw/data/open-issues.json` and `/tmp/gh-aw/data/open-prs.json`, identify any open blockers matching at least one of these criteria:
- Open issues or pull requests labeled `blocked`, `priority: critical`, or `priority: high`
- Open non-draft pull requests with failing required CI checks in `statusCheckRollup` (`FAILURE`, `TIMED_OUT`, or `ACTION_REQUIRED`) or `CHANGES_REQUESTED` review decisions

### 2. Evaluate No-Op Condition

If `/tmp/gh-aw/data/new-issues.json` has zero non-report issues, `/tmp/gh-aw/data/merged-prs.json` has zero merged pull requests, and there are zero open blockers, do not create an issue. Instead, call:
`noop("No updates or open blockers in last 24 full hours (<window_start_utc> to <window_end_utc>)")`

### 3. Format and Publish the Report

When activity or blockers exist, call `create-issue` (with body length between 20 and 65,000 characters) using the deduplication key `daily-activity-report:<YYYY-MM-DD>` and follow these formatting rules:
- Use `###` (h3) for main sections and `####` (h4) for subsections (never `#` or `##`).
- Use GitHub alerts (`> [!NOTE]`, `> [!WARNING]`, `> [!CAUTION]`) instead of emoji status markers.
- Group items by category (**Open Blockers**, **Merged Pull Requests**, **New Issues**) and note "Unclassified" when labels or metadata are absent.
- Wrap detailed per-item breakdowns in `<details><summary>...</summary>` blocks while keeping headline metrics and critical blockers visible at the top.

## Safe Outputs

- Use `create-issue` (max 1) to publish the daily report issue when activity or blockers exist.
- Call `noop` with the evaluated UTC window when no qualifying activity or blockers exist.
