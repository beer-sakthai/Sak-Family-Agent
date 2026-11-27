---
name: SakJules-workflow-security-zizmor
version: 1.0.0
description: "Audit GitHub Actions workflows with Zizmor AST analysis, enforce full SHA-256 action pinning, and verify StepSecurity Harden-Runner runtime policies across .github/workflows/."
category: security
tags:
- automation
- devsecops
- github-actions
- security
- zizmor
---

# Workflow Security & Zizmor Audit

Use this skill when auditing, creating, or modifying GitHub Actions workflows in `.github/workflows/` to enforce supply-chain security, prevent script injection, and ensure zero unpinned third-party actions.

## Goal

Ensure all GitHub Actions workflows satisfy top-tier DevSecOps benchmarks:
1. **Strict SHA-Pinning**: Every third-party action must pin an immutable 40-character commit SHA (e.g., `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683`), never mutable tags (`@v4`, `@main`).
2. **Minimal Permissions**: Workflows must declare explicit top-level `permissions:` (preferably `contents: read`) or explicit per-job permissions.
3. **AST Static Analysis via Zizmor**: Identify expression injections (`${{ github.event... }}` in `run:`), dangerous trigger combinations, and insecure runner defaults.
4. **StepSecurity Harden-Runner**: Verify outbound network containment policies.

## Prerequisites

- Python 3.11+ / `uv`
- `zizmor` (runnable via `uvx zizmor .github/workflows/`)

## Step-by-Step Workflow

### 1. Run Zizmor Workflow Audit

Scan the repository workflows for known anti-patterns:
```bash
uvx zizmor .github/workflows/
```

Key vulnerability classes to inspect:
- **Artipacked / Template Injection**: Untrusted inputs directly interpolated into shell scripts (`run: echo "${{ github.event.issue.title }}"`). Always pass untrusted context via environment variables.
- **Dangerous Triggers**: `pull_request_target` with explicit checkouts of untrusted code.
- **Unpinned Actions**: Third-party actions referencing floating tags instead of full git SHAs.

### 2. Verify Action SHA-Pinning

Every `uses:` line referencing external repositories must specify a 40-character hexadecimal SHA with an inline comment indicating the version:

```yaml
# Correct:
- name: Check out repository
  uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

# Forbidden (triggers security gate failure):
- name: Check out repository
  uses: actions/checkout@v4
```

Verify pinning across the repo:
```bash
python3 scripts/audit_repo_security.py
```

### 3. Audit Permissions Blocks

Ensure workflows declare top-level restrictive permissions:
```yaml
permissions:
  contents: read
```
If a specific job requires write access (e.g., releasing or publishing artifacts), grant it strictly within that specific job block, not globally.

### 4. StepSecurity Harden-Runner Validation

Verify network calls within CI runners:
```yaml
- name: Harden Runner
  uses: step-security/harden-runner@4d991eb9b005fe389e0001aa02112d38702427e6 # v2.11.0
  with:
    egress-policy: audit # or block
```

## Remediation Recipe

1. Replace unpinned action tags using `gh api repos/{owner}/{repo}/commits/{tag}` to resolve the exact commit SHA.
2. Replace inline bash expressions with `env:` declarations.
3. Run `uv run ruff check` and `make lint` on modified workflow automation scripts.
