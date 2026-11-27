---
name: SakJules-triage-issues
version: 1.1.0
description: "Triage GitHub issues for Sak-Family-Agent and connected repositories: propose labels (type, priority, area, status), check duplicates, verify bug reproduction details, and draft maintainer triage recommendations."
category: devops
tags:
- automation
- github
- issues
- triage
---

# Triage GitHub Issues

Triage here is systematic **classification, duplicate checking, and completeness verification**. Propose recommendations for maintainer review without mutating issues without approval.

## Goal

Given an issue number (or several), deliver a clear triage recommendation:
1. Classification labels across standard axes (type, priority, component/area).
2. Detection of potential duplicate issues or existing PRs.
3. Verification of bug reproduction completeness (logs, environment, reproduction steps).
4. A draft triage comment for the author or reviewer.

## Prerequisites

- `gh` CLI authenticated for the target repository (default: current repository or `beer-sakthai/Sak-Family-Agent`).

## Workflow

### 1. Fetch Issue Details

```bash
# View target issue in current or specified repo:
gh issue view <issue-number> [--repo <owner/repo>] --json number,title,body,author,labels,comments,createdAt
```

### 2. Inspect Valid Repository Labels Live

Read labels dynamically from the target repo rather than assuming taxonomy:
```bash
gh label list [--repo <owner/repo>] --limit 100
```

### 3. Check for Duplicates & Overlapping Open PRs

```bash
# Search issues for overlapping keywords:
gh issue list --search "<key phrases>" --state all --limit 10

# Check open PRs to see if a fix is already in flight:
gh pr list --state open --limit 20
```

### 4. Evaluate Completeness

For bug reports, verify:
- Expected vs. actual behavior is stated.
- Steps to reproduce are present.
- Environment details (OS, Python version, package version) are documented.
- Relevant logs or stack traces are included (scrubbing secrets).

### 5. Propose Recommendations

Present a structured triage proposal:
- **Labels Proposed**: `type:*`, `priority:*`, `area:*`.
- **Duplicates**: Link any candidate issues or PRs.
- **Missing Information**: Specific questions to ask the reporter if blocked.
- **Recommended Action**: E.g., Assign to persona/maintainer, request info, mark duplicate, or route to backlog.
