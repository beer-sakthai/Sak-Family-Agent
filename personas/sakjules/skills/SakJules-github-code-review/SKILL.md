---
name: SakJules-github-code-review
version: 1.1.0
description: Systematic protocol for reviewing local git diffs, evaluating GitHub pull requests, and submitting structured reviews.
category: devops
tags:
- automation
- code
- github
- review
---

# GitHub Code Review Protocol

Standard operating procedure for auditing local changes pre-push and conducting pull request reviews on GitHub.

## 1. Review Invariants & Standards
- **Quality Gates First**: Verify tests, linter passes, and security scans locally before approving or submitting a PR.
- **Coverage Floor**: Enforce project test coverage floor ($\ge 96\%$). Any regression requires new tests.
- **No Secrets or Debug Residuals**: Strict denial for committed API keys, hardcoded credentials, or stray debug print statements.
- **Never Auto-Merge**: Always leave pull requests open for manual review and merge by Beer.

## 2. Review Lifecycle
1. **Pre-Review Scope**: Inspect diff stat and commit history: `git diff main...HEAD --stat`.
2. **Detailed Diff Audit**: Check for logical soundness, error handling, and performance regressions.
3. **CI Status Check**: Query remote workflow status using `gh pr checks <PR_NUMBER>`.
4. **Formulate Feedback**: Structure findings into actionable recommendations with file and line references.

## 3. Feedback Structure
- Summary: High-level overview of changes and risk assessment.
- Positives: What was executed well.
- Findings: Grouped by severity (Critical / High / Medium / Low).
- Actionable Next Steps: Concrete commands or patches to resolve findings.

## 4. References & Templates
- Detailed commands & API recipes: [Code Review Playbook](references/code-review-playbook.md)
- Markdown review output format: [Review Output Template](references/review-output-template.md)
