# GitHub Repository Settings & Governance Runbook

**SakJules · Master of Automation & CI/CD.**

This runbook documents the repository settings that require manual maintainer actions by **Beer** (repository admin) via the GitHub web UI, as external settings cannot be modified via git commits.

---

## 1. Required Status Checks De-duplication

### Problem
PR #1886 and `.github/workflows/repository-security-quality.yml` currently execute a redundant `quality` job (named **"Quality gates"**) alongside `ci.yml`. `ci.yml` already runs Ruff, Mypy, Bandit, and Pytest across Python 3.11 and 3.12 with the $\ge 96\%$ coverage floor. PRs currently pay for the entire test suite twice.

### Action for Beer
1. Navigate to: **GitHub Repository → Settings → Branches**.
2. Under **Branch protection rules**, edit the rule for branch `main`.
3. Locate the **Require status checks to pass before merging** section.
4. In the list of required status checks:
   - **Keep:** `ci / Test and Lint (Python 3.11)` and `ci / Test and Lint (Python 3.12)`
   - **Remove:** `Quality gates` (or `repository-security-quality / quality`)
5. Click **Save changes**.
6. *Outcome:* Once removed, the duplicate `quality` job in `.github/workflows/repository-security-quality.yml` can be retired safely without blocking future PRs with HTTP 405 errors.

---

## 2. OpenSSF Scorecard Non-Commit Hardening

To elevate the OpenSSF Scorecard score to 10/10 across all categories:

### A. Branch Protection Settings
1. In **Settings → Branches → Branch protection rules (`main`)**:
   - Check **Require a pull request before merging**.
   - Check **Require approvals** (minimum 1 or 2).
   - Check **Dismiss stale pull request approvals when new commits are pushed**.
   - Check **Require conversation resolution before merging**.
   - Check **Require signed commits** (optional, recommended).
   - Check **Require linear history**.
   - Ensure **Allow force pushes** is **Disabled**.
   - Ensure **Allow deletions** is **Disabled**.

### B. Code Review Policy
- Scorecard's `Code-Review` check assesses human review on changes merged to `main`.
- All automated bot and subagent PRs remain in **Draft** or **Awaiting Review** status specifically for Beer's manual review.

### C. OpenSSF Best Practices Badge (CII)
- Follow the completed questionnaire in [`docs/cii-best-practices-answers.md`](./cii-best-practices-answers.md) to register and claim the passing badge at [bestpractices.coreinfrastructure.org](https://bestpractices.coreinfrastructure.org).

---

## 3. Auto-Merge Prohibition Protocol

- **Absolute Rule:** In accordance with the House of Sak Operating Contract, `gh pr merge` and `--auto` are strictly prohibited in all automated workflows and agent scripts.
- Every Pull Request submitted by `SakJules` or any sibling agent will conclude with a verified CI/CD report and remain open for Beer's review and manual click-to-merge.
