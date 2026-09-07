# Verification and Integration Procedure

## Change classification

1. Inspect `git status`, `git branch -vv`, `git log -5`, and the relevant files.
2. Identify whether the change affects Python runtime behavior, the dashboard, persona/skill content, documentation, training, infrastructure, or CI/security.
3. Select focused tests before broad checks. Preserve a clean baseline where failures are likely.

## Minimum verification

| Change type | Required checks |
|---|---|
| Core Python behavior | Focused pytest tests, `git diff --check`, `make lint`, strict mypy, Bandit, and the relevant pytest/coverage command. |
| Security or guardrails | Focused regression tests, Bandit, secret-pattern review of added lines, path/network/auth boundary checks, and the full relevant suite. |
| Dashboard | Relevant Vitest tests, ESLint, TypeScript/build checks, and `git diff --check`. |
| Documentation or README | Markdown structure, link targets, balanced code fences, factual-count review, and `git diff --check`. |
| CI or workflow | YAML syntax review, action/version/permission review, and a pull request run of the affected workflow. |
| Training or data | Schema/fixture checks, deterministic smoke tests, and explicit review of credentials, generated artifacts, and dataset paths. |

Treat warnings as information unless they indicate a real regression. Never silently suppress a failing check.

## Protected `main` workflow

Use this sequence when the user requests commit, push, merge, or branch consolidation:

```text
inspect worktree → create focused branch → edit → verify → commit
→ push branch → open PR to main → wait for required checks
→ inspect PR status → merge PR → delete temporary branch
→ fetch --prune → verify origin/main and clean worktree
```

Direct pushes to `main` may be rejected by repository rules. Do not force-push or bypass required checks. Use `gh pr create`, `gh pr view`, and `gh pr merge` through the GitHub CLI.

Before deleting any source branch, confirm its tip is an ancestor of the merged `main` commit. Delete only fully merged branches or branches the user explicitly authorizes.

## Completion report

Include:

- Files and behavior changed.
- Focused and full checks with pass/fail results.
- Any environment-specific limitations, including Node or dependency engine mismatches.
- Commit SHA and pull-request URL.
- Final `origin/main` SHA, worktree status, and remaining remote branches.

For README status bars, distinguish dynamic workflow badges from dated local snapshots and list the commands behind every quantitative claim.
