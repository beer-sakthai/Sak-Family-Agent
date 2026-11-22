SakJules · Master of Automation & CI/CD.

# GitHub Actions Workflow Plan Builder

**Repository:** `beer-sakthai/Sak-Family-Agent`  
**Default branch:** `main`  
**Inventory basis:** `.github/workflows/` on 2026-11-18  
**Workflow-related files:** 158 total — 144 ordinary YAML workflows, 7 generated gh-aw lockfiles, and 7 gh-aw source Markdown workflows.

## Purpose

This document is the working plan for maintaining, simplifying, securing, and extending the repository's GitHub Actions estate. It treats GitHub Agentic Workflows (`.md` source plus generated `.lock.yml`) as a paired artifact and keeps ordinary Actions workflows separate from generated files.

The plan is intentionally staged. First establish an accurate baseline and ownership map. Then reduce duplication and policy risk. Only after those gates pass should the repository change workflow behavior or add new automation.

## Complete workflow inventory

### Core CI, package, and project validation

| File | Workflow | Trigger | Main responsibility |
|---|---|---|---|
| `ci.yml` | CI | Push and pull request to `main` | Python test matrix on 3.11 and 3.12 |
| `pylint.yml` | Pylint | Push and pull request to `main` | Pylint/build validation on 3.11 and 3.12 |
| `apps.yml` | Apps | Path-filtered push and pull request | Dashboard, workflow framework, and contracts checks |
| `subprojects.yml` | Sub-project tests | Path-filtered push and pull request | `sakthai-chat-cli` and Teams Copilot MCP checks |
| `sak-family-agent-contract.yml` | Sak Family agent contract | Path-filtered push and pull request plus manual | Persona and agent contract parity |
| `verify-assets.yml` | Verify Public Hugging Face Assets | Daily schedule and manual | Validate published Hugging Face assets |
| `run-evals.yml` | Run Evals | Weekly schedule and manual | Run evaluations, aggregate results, publish summary, and check regressions |
| `agent-self-evolution.yml` | agent-self-evolution | Path-filtered push and pull request plus manual | Evolution-package tests |
| `copilot-setup-steps.yml` | Copilot Setup Steps | Manual and changes to its own file | Prepare Copilot development environment |
| `manual.yml` | Manual workflow | Manual | Simple operator-triggered greeting/smoke workflow |

### Security, supply chain, and code quality

| File | Workflow | Trigger | Main responsibility |
|---|---|---|---|
| `bandit.yml` | Bandit | Push, pull request, and weekly schedule | Python security scanning |
| `codeql.yml` | CodeQL Advanced | Push, pull request, weekly schedule, and manual | CodeQL analysis for Actions, JavaScript/TypeScript, and Python |
| `dependency-audit.yml` | Dependency Audit | Dependency-related pull requests and weekly schedule | `pip-audit` dependency vulnerability scan |
| `dependency-review.yml` | Dependency Review | Pull requests to `main` | Review dependency changes |
| `secret-scan.yml` | Secret Scan | Push, pull request, daily schedule, and manual | Gitleaks scan and branch sweep |
| `ossar.yml` | OSSAR | Push, pull request, and weekly schedule | OSSAR supply-chain scan |
| `scorecard.yml` | Scorecard supply-chain security | Branch-protection event, push, and weekly schedule | OpenSSF Scorecard analysis |
| `sonarcloud.yml` | SonarCloud analysis | Push, pull request, and manual | SonarCloud analysis and PR decoration |
| `repository-security-quality.yml` | Repository Security and Quality | Pull requests to `main` | Skill validation, quality gates, and security gates |
| `code-scanning-cleanup.yml` | Code scanning cleanup | Manual | Dry-run or apply cleanup/dismissal of code-scanning analyses |
| `continuous-security.yml` | Continuous Security Scan | Manual | DevSecOps scan |

### Review, maintenance, and repository operations

| File | Workflow | Trigger | Main responsibility |
|---|---|---|---|
| `code-review.yml` | Gemini AI Code Reviewer | New issue comments containing `/gemini-review` | Review pull-request changes with Gemini using `GEMINI_API_KEY` |
| `daily-pr-review.yml` | Daily PR review and branch cleanup | Daily schedule and manual | Review pull requests and optionally delete safe stale branches |
| `daily-workspace-status.yml` | Daily workspace status and PR conflict monitor | Daily schedule and manual | Report workspace and PR conflict status |
| `branch-cleanup.yml` | Branch cleanup | Manual | Dry-run or apply deletion of eligible branches |
| `stale.yml` | Mark stale issues and pull requests | Daily schedule | Mark and close stale issues and pull requests |
| `labeler.yml` | Labeler | `pull_request_target` | Apply labels based on changed files |
| `summary.yml` | Summarize new issues | New issues | Summarize newly opened issues |
| `agentics-maintenance.yml` | Agentic Maintenance | Daily schedule, manual, and reusable workflow call | Maintain agentic workflows, labels, reports, and safe outputs |

<details>
<summary>Complete ordinary YAML file list (144 files)</summary>

- `actions-usage-audit.yml`
- `actions-version-updater.yml`
- `activity-readme.yml`
- `add-badges.yml`
- `agent-self-evolution.yml`
- `agentics-maintenance.yml`
- `ai-code-guard.yml`
- `ai-pr-opener-bot.yml`
- `apps.yml`
- `auto-assign.yml`
- `auto-cancel-redundant.yml`
- `auto-close-issues.yml`
- `auto-contrib-pr.yml`
- `auto-issue-bot.yml`
- `auto-label-merge-conflicts.yml`
- `auto-merge-bot.yml`
- `auto-request-review.yml`
- `auto-reviewer-assign.yml`
- `autodocs.yml`
- `autofix.yml`
- `autoheal-ci.yml`
- `autolabeler-codeowners.yml`
- `automated-pr-maintenance.yml`
- `automerge-pr.yml`
- `autoupdate-branches.yml`
- `bandit.yml`
- `bot-check-action.yml`
- `branch-cleanup.yml`
- `branch-sync.yml`
- `cache-cleanup.yml`
- `checkbox-trigger.yml`
- `ci-dokumentor.yml`
- `ci.yml`
- `code-review.yml`
- `code-scanning-cleanup.yml`
- `codeowners-bot.yml`
- `codeql.yml`
- `config-git-actions-bot.yml`
- `continuous-benchmark.yml`
- `continuous-security.yml`
- `copilot-setup-steps.yml`
- `daily-pr-review.yml`
- `daily-workspace-status.yml`
- `dependabot-auto-merge-cli.yml`
- `dependabot-auto-merge.yml`
- `dependabot-automerge.yml`
- `dependabot-fetch-metadata.yml`
- `dependabot-helper.yml`
- `dependabot-issue.yml`
- `dependabot-workflow.yml`
- `dependafix-ai-remediation.yml`
- `dependency-audit.yml`
- `dependency-review.yml`
- `dependfix-security-auto-fix.yml`
- `enable-automerge-dependabot.yml`
- `fixed-issues-labeler.yml`
- `gemini-actions.yml`
- `gemini-code-review-action.yml`
- `gemini-review-bot.yml`
- `generate-roadmap.yml`
- `generator-generic-ossf-slsa3-publish.yml`
- `genshdoc.yml`
- `gh-actions-auto-docs.yml`
- `gh-actions-docs.yml`
- `gh-actions-documenter.yml`
- `git-as-github-actions-bot.yml`
- `git-auto-commit.yml`
- `git-flow-action.yml`
- `git-pr-release.yml`
- `gitflow-lifecycle.yml`
- `github-bot-auto-answer.yml`
- `github-ci-bot.yml`
- `github-workflow-sync.yml`
- `google-chat-notification.yml`
- `huggingface-integration.yml`
- `issue-bot.yml`
- `labeler.yml`
- `licensed-audit.yml`
- `lint-check.yml`
- `manual.yml`
- `merge-pr-action.yml`
- `merge-pr.yml`
- `no-free-usage.yml`
- `ossar.yml`
- `patchbot-scanner.yml`
- `pipeline-healer.yml`
- `playwright-test-failure-triage-bot.yml`
- `pr-automation.yml`
- `pr-codename.yml`
- `pr-comment-trigger.yml`
- `pr-label-checker.yml`
- `pr-lint.yml`
- `pr-preview.yml`
- `pr-triage-bot.yml`
- `pull-request-code-review-bot.yml`
- `pylint.yml`
- `python-lint-sarif.yml`
- `rational-test-server.yml`
- `release-from-tag.yml`
- `renovate.yml`
- `repo-file-sync.yml`
- `repository-security-quality.yml`
- `reusable-app-token.yml`
- `reusable-comment-pr.yml`
- `reusable-deployment.yml`
- `reusable-dispatch-method.yml`
- `reusable-manual-approval-gate.yml`
- `reusable-pr-deploy.yml`
- `reusable-trigger-workflow-wait.yml`
- `reusable-update-pr-branches.yml`
- `reusable-workflow-dispatch-wait.yml`
- `reusable-workflow-dispatch.yml`
- `run-evals.yml`
- `runner-disk-cleaner.yml`
- `safe-dependabot.yml`
- `sak-family-agent-contract.yml`
- `scorecard.yml`
- `secret-scan.yml`
- `self-approve.yml`
- `semantic-tagging.yml`
- `set-bot-github-user.yml`
- `setup-github-actions-bot.yml`
- `setup-github-app-as-bot.yml`
- `sonarcloud.yml`
- `stale.yml`
- `step-ci.yml`
- `subprojects.yml`
- `summary.yml`
- `sync-branch-action.yml`
- `the-auditor.yml`
- `update-pr-branches-from-main.yml`
- `update-pr-reminder.yml`
- `verified-bot-commit.yml`
- `verify-assets.yml`
- `wait-for-workflow.yml`
- `weekly-workflow-sync-validation.yml`
- `weekly-workflow-validation.yml`
- `wiki-page-maintenance.yml`
- `wiki-sync.yml`
- `workflow-conclusion.yml`
- `workflow-immortality.yml`
- `workflow-queue.yml`
- `workflow-run-wait.yml`
- `workflow-status-indicator.yml`

</details>

### GitHub Agentic Workflows: source Markdown

These seven files are declarative sources. They are not directly executable until compiled by `gh aw`.

| Source | Purpose | Output policy |
|---|---|---|
| `code-simplifier.md` | Find one worthwhile simplification and open a draft PR | Draft PR, no-op when no safe change exists |
| `daily-activity-report.md` | Summarize issues, merged PRs, and blockers over the last 24 hours | At most one issue or no-op |
| `daily-doc-sync.md` | Detect documentation drift and propose updates | Restricted documentation-only PR or no-op |
| `issue-triage.md` | Classify, deduplicate, clarify, and assign newly opened issues | Labels, one comment, optional assignment, or no-op |
| `repo-maintainer.md` | Select and validate one bounded maintenance improvement | Restricted draft PR or no-op |
| `skill-pr-reviewer.md` | Review pull requests with installed expert skills | Review comments or no-op |
| `weekly-agents-md-sync.md` | Keep root `AGENTS.md` aligned with repository changes | Review-gated `AGENTS.md`-only PR or no-op |

### GitHub Agentic Workflows: generated lockfiles

These seven generated files are the compiled runtime artifacts currently checked in:

- `code-simplifier.lock.yml`
- `daily-activity-report.lock.yml`
- `daily-doc-sync.lock.yml`
- `issue-triage.lock.yml`
- `repo-maintainer.lock.yml`
- `skill-pr-reviewer.lock.yml`
- `weekly-agents-md-sync.lock.yml`

All seven sources currently have matching lockfiles. For every source change, regenerate the matching lockfile and validate with `gh aw compile --no-emit --validate` before emitting or committing generated output.

## Current parity and security audit

The current repository contains **7 gh-aw source workflows and 7 matching lockfiles**. `gh aw compile --no-emit --validate --json` reported all seven sources as valid with zero parity or compilation errors. It emitted two warnings for `skill-pr-reviewer.md` that require follow-up:

- Its `threat-detection` configuration names the custom `gemini` engine, but threat detection only supports the built-in `copilot` engine unless the configuration is changed or detection is disabled.
- Its `update_cache_memory` path has explicit cache-write access; review whether that is safe for every trigger, especially untrusted pull-request execution. Prefer read-only cache mode for untrusted execution unless the write boundary is explicitly justified.

The repository snapshot contains **144 ordinary YAML workflows**, not the 30-workflow count from the earlier baseline. A Zizmor 1.32.0 `--pedantic` audit completed across all 144 files and reported 260 findings. These are audit findings, not automatically confirmed vulnerabilities:

| Rule | Findings | Affected workflows | Severity profile | Recommended action |
|---|---:|---:|---|---|
| `excessive-permissions` | 91 | 64 | 90 high, 1 medium | Move write permissions from workflow scope to the smallest job that needs them; confirm each write is required |
| `undocumented-permissions` | 112 | 98 | Low | Add concise comments explaining non-read permissions |
| `template-injection` | 17 | 5 | Low | Review event-derived values used in shell or action inputs; pass untrusted data through environment variables and quote it |
| `anonymous-definition` | 37 | 33 | Informational | Add job or reusable-workflow names where useful for auditability |
| `stale-action-refs` | 2 | 2 | Low | Refresh the stale pinned references after checking release provenance |
| `superfluous-actions` | 1 | 1 | Informational | Remove the redundant action if behavior is unchanged |

The audit did not modify workflows. Treat the 90 high-severity `excessive-permissions` findings as the first remediation queue, but verify actual job behavior before narrowing permissions. In particular, do not bulk-replace write permissions in automation that intentionally creates releases, updates branches, or comments on pull requests.

## Baseline observations

The repository has strong coverage of the usual CI and security concerns, but the workflow estate is large enough that duplication and operational overlap are now maintenance risks. There are several daily schedules, multiple security scanners, multiple PR-review mechanisms, and both ordinary Actions and gh-aw automations that can create comments, issues, labels, branches, or pull requests.

The most important correctness boundary is generated-file parity: a gh-aw Markdown source and its lockfile must be treated as one change. The second boundary is permissions: workflows that only read repository state should remain read-only, while workflows that write labels, comments, issues, branches, or pull requests need an explicit and reviewed reason for each write permission.

The Gemini review workflow has a repository-specific regression history: YAML was previously excluded, which prevented review of workflow-only pull requests. The current plan must preserve YAML review coverage and should add a fixture-based test for the filter before changing it again.

## Plan builder

Use one row per proposed workflow change. Do not combine unrelated workflow changes into one PR.

| ID | Work item | Priority | Owner lane | Depends on | Definition of done |
|---|---|---:|---|---|---|
| W0 | Record workflow inventory and ownership | P0 | SakJules | None | This document is current; every file has an owner, trigger, purpose, and risk class |
| W1 | Add automated workflow metadata validation | P0 | SakJules | W0 | CI detects duplicate workflow names, missing names, invalid triggers, missing permissions, and malformed YAML |
| W2 | Add gh-aw source/lock parity validation | P0 | SakJules | W0 | CI fails when a `.md` source has a stale or missing lockfile; validation uses `gh aw compile --validate` |
| W3 | Review write permissions and safe-output boundaries | P0 | SakJules + repository owner | W0 | Each workflow has least-privilege permissions; write-capable jobs document their target and reason |
| W4 | Add regression coverage for Gemini review file filtering | P1 | SakJules | W0 | A small test proves `.yml`, `.yaml`, and `.lock.yml` remain reviewable while prose and npm lockfiles remain excluded |
| W5 | Resolve `skill-pr-reviewer` gh-aw warnings | P0 | SakJules + repository owner | W2, W3 | Threat detection uses a supported engine or is explicitly disabled, and cache writes are constrained for untrusted triggers |
| W6 | Decide whether to enable `code-simplifier` | P1 | SakJules + repository owner | W2, W3 | The source and existing lockfile are validated, and its safe-output behavior is documented before activation |
| W7 | Consolidate overlapping daily operational reports | P1 | SakTan + SakJules | W0, W3 | A schedule map shows one authoritative owner for each report; duplicate issue/comment creation is removed or intentionally retained |
| W8 | Consolidate security scan responsibilities | P1 | SakJules | W3 | Each scanner has a distinct purpose, cadence, and required-check decision; redundant scans are justified or retired |
| W9 | Define the required-check policy | P0 | Repository owner | W3, W8 | `main` protection lists only stable, actionable checks; advisory and scheduled checks are not accidentally merge blockers |
| W10 | Add workflow runtime and cost observability | P2 | SakJules | W0, W7 | Monthly report captures scheduled-run volume, failures, duration, and agentic-workflow usage/cost signals |
| W11 | Document operator runbooks | P2 | SakJules | W2, W3, W9 | Manual inputs, dry-run behavior, rollback steps, and secret requirements are documented for destructive or write-capable workflows |
| W12 | Add safe deployment gates for workflow changes | P1 | SakJules | W1, W2, W9 | Workflow changes run syntax, security, gh-aw compilation, and targeted tests before merge |

## Recommended execution order

### Phase 1 — Make the inventory enforceable

Complete W1, W2, and W3 first. The goal is not to change behavior. It is to ensure that every workflow has valid syntax, explicit permissions, an identified owner, and a source/lock parity check where gh-aw is used.

The first PR should add or extend static validation only. It should report findings without changing existing schedules or permissions unless a concrete security defect is confirmed.

### Phase 2 — Protect known behavior

Complete W4, W5, and W6. Preserve the Gemini reviewer behavior that allows YAML reviews. Resolve the `skill-pr-reviewer` engine and cache warnings, then validate the existing `code-simplifier` source/lock pair and document its safe-output restrictions before changing its schedule.

Add fixture tests for the workflow filter and gh-aw source/lock mapping. These tests should be hermetic and should not call Gemini, GitHub write APIs, or scheduled workflows.

### Phase 3 — Reduce operational overlap

Complete W7 and W8 by building a trigger-and-output matrix. For each workflow, record whether it creates an issue, comment, label, branch deletion, pull request, or external report. Any two workflows with the same trigger, target, and output should be merged, narrowed, or explicitly documented as complementary.

Do not disable a security or maintenance workflow solely because another workflow has a similar name. First compare coverage, credentials, required status checks, and failure behavior.

### Phase 4 — Make protection intentional

Complete W9 and W12. Required checks should be stable, fast enough for pull requests, and directly tied to merge safety. Scheduled-only scans should report findings without unexpectedly blocking unrelated pull requests unless the repository explicitly wants that policy.

Every workflow change should pass YAML parsing, action pinning checks, secret scanning, gh-aw compilation where applicable, and the targeted repository test suite.

### Phase 5 — Improve operations

Complete W10 and W11 after the workflow surface is stable. Add operational dashboards or reports only after defining retention, privacy, and ownership. Document manual workflows with their dry-run and apply modes so destructive actions are not accidentally executed.

## Required validation gates for future workflow PRs

A workflow pull request is ready for review only when all applicable gates pass:

1. `git diff --check` passes and the diff contains no secrets.
2. Every edited YAML workflow parses successfully.
3. Every referenced action remains pinned according to repository policy.
4. `gh aw compile --validate` passes when a gh-aw source or lockfile is changed.
5. Source Markdown and generated lockfiles are changed together for gh-aw updates.
6. Permissions are least-privilege and write permissions have a stated target.
7. Trigger filters and path filters are tested against the intended files.
8. The relevant CI, security, and contract checks pass.
9. Manual or destructive workflows retain a dry-run path and explicit apply control.
10. The PR description states what was intentionally not changed.

## Change record template

Copy this template into a work item or PR before editing a workflow:

```markdown
### Workflow change

- **Workflow(s):**
- **Source/lock pair:**
- **Owner:**
- **Trigger(s):**
- **Permissions changed:**
- **Secrets or external services:**
- **Safe outputs or destructive effects:**
- **Why this change is needed:**
- **What is intentionally out of scope:**

### Validation

- [ ] YAML parse
- [ ] Action pin/security validation
- [ ] `gh aw compile --validate` when applicable
- [ ] Targeted tests
- [ ] Full required checks
- [ ] Manual dry-run, if applicable
```

## Success criteria

The workflow estate is in a healthy state when every executable workflow has a named owner and documented purpose, every gh-aw source has a matching validated lockfile, write permissions are justified, duplicate scheduled outputs are eliminated or intentional, required checks are stable, and a workflow-only pull request receives the expected automated review instead of being filtered to zero files.
