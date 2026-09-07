---
name: Sak-repository-quality
category: quality
description: >-
  Plan, implement, test, and integrate high-quality changes in Sak-Family-Agent.
  Use for repository maintenance, code review, tests, documentation, skill
  content, dashboard work, generated contracts, CI validation, pull requests,
  and release-ready verification.
version: "1.0.0"
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - quality
      - testing
      - review
      - ci
      - documentation
    related_skills:
      - Sak-repository-security
---

# Sak-Family-Agent Quality

Use this skill to deliver a small, complete, reviewable repository change. Follow the repository's canonical commands and documentation rather than guessing from a generic stack. Treat a green local command as evidence for that command only; distinguish it from live pull-request status.

## Establish the change boundary

1. Read `AGENTS.md`, `CLAUDE.md`, `PLAN.md`, the closest component documentation, and the relevant workflow before editing.
2. Inspect the branch, worktree, recent history, remote `main`, and open pull requests. Do not create a duplicate or overlapping pull request.
3. Classify the change as core runtime, persona/skill content, dashboard, training, infrastructure, documentation, or CI/security. Keep unrelated cleanup out of the patch.
4. Identify the source of truth and its downstream copies, generated files, contracts, or deployment surfaces before making a change.

## Make the smallest correct change

Keep behavior, documentation, tests, and generated artifacts coherent. Preserve existing formatting, naming, safety controls, action pins, dependency locks, and coverage thresholds. Update canonical documentation when a public command, configuration, interface, or operator workflow changes, and link to the authoritative source instead of copying facts into multiple files.

When code changes behavior, add or revise tests for normal operation, errors, boundaries, and the regression that motivated the change. Make tests deterministic and isolated: use temporary directories and injected dependencies, and do not make unit tests depend on live credentials, a network registry, external MCP servers, a real home directory, or timing.

## Select checks by surface

| Change surface | Minimum focused verification |
| --- | --- |
| Shared or persona skills | Validate frontmatter and naming; run persona composition if shared skill delivery or composition changes. |
| Core Python runtime or tests | Run focused pytest first, then the CI-equivalent Ruff, format, strict mypy, Bandit, and coverage-enforced pytest gates. |
| Dashboard or contracts | Use `apps/sak_agent_dashboard/package.json` and `make dashboard-test`; regenerate and check contract types whenever `web/contracts.py` changes. |
| CI, workflows, dependencies, or Docker | Validate syntax and pinning; use the documented lockfile/hash generator; confirm the relevant trigger and permissions. |
| Documentation-only | Check Markdown structure, links, fenced commands, path references, and every factual count or date against the current tree. |
| Guardrails, auth, subprocess, paths, or integrations | Apply `Sak-repository-security` and include adversarial regression coverage. |

## Verify the diff

1. Review `git diff --check` and the complete staged diff before committing.
2. Confirm that no generated output is stale, no secret has entered the change, and no supported persona copy is unintentionally divergent.
3. Run the narrowest relevant test first, then the broader gates required by the surface. Record exact commands and outcomes.
4. If a command fails, determine whether the failure predates the change using a clean baseline where practical. Do not hide failures, lower standards, or claim passing status without evidence.

For shared skills, use:

```bash
uv run sakthai skills validate --source library
uv run sakthai skills validate --naming
make compose-personas
```

## Integrate through GitHub

Use a descriptive conventional commit and an explicit `main` target. Rebase on the latest `origin/main` before opening the pull request when required by repository policy. Include a concise change summary, rationale, validation commands, and limits in the pull-request body.

Wait for all required GitHub checks to reach success. Never bypass branch protection. After merge, verify the merged commit on `origin/main`, that the worktree is clean, and that the temporary branch is deleted only after its changes are present on `main`.

## Completion evidence

Report the changed source of truth, user-visible effect, local validation results, live pull-request and merge status, commit and pull-request links, and remaining caveats. Do not describe historical CI snapshots as current status.
