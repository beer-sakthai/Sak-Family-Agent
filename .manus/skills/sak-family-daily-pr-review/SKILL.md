---
name: sak-family-daily-pr-review
description: "Review open pull requests, verify required checks, summarize risks, and safely clean up stale or merged branches in beer-sakthai/Sak-Family-Agent. Use for daily repository maintenance, PR triage, branch hygiene, check monitoring, and post-merge cleanup."
---

# Sak-Family Daily PR Review

Run a repeatable, evidence-based daily maintenance pass for `beer-sakthai/Sak-Family-Agent`. Separate review from mutation: inspect all open PRs and branch candidates first, produce a report, and only merge or delete refs when the requested policy and safety gates are satisfied.

## Preconditions

1. Work from the repository root and read `AGENTS.md`, `CLAUDE.md`, `PLAN.md`, the maintainer skill, and the nearest workflow/component guidance before changing anything.
2. Confirm `gh auth status`, the repository identity, the default branch, and the current worktree status.
3. Never operate on a dirty worktree. If local changes exist, report them and stop before branch switching, rebasing, merging, or deletion.
4. Treat `main` as protected integration branch. Use pull requests for integration; never force-push or bypass branch protection.
5. Default all discovery and cleanup classification to dry-run. Require explicit user authorization before merge, branch deletion, or other destructive action.

## Daily review workflow

### 1. Inventory

Collect:

```bash
gh pr list --repo beer-sakthai/Sak-Family-Agent --state open --limit 100 \
  --json number,title,headRefName,baseRefName,author,isDraft,mergeStateStatus,reviewDecision,statusCheckRollup,updatedAt,url

gh api repos/beer-sakthai/Sak-Family-Agent --jq '{default_branch: .default_branch, archived: .archived, disabled: .disabled}'
git status --short --branch
git branch -a -vv
```

Group PRs by draft state, mergeability, review decision, check state, age, and head branch. Do not infer a green check from a stale local log or a single successful job.

### 2. Review each open PR

For every PR, inspect the diff and evidence:

```bash
gh pr view <number> --repo beer-sakthai/Sak-Family-Agent --json title,body,files,commits,reviews,comments,reviewDecision,mergeStateStatus,statusCheckRollup,baseRefName,headRefName,url
gh pr diff <number> --repo beer-sakthai/Sak-Family-Agent
gh pr checks <number> --repo beer-sakthai/Sak-Family-Agent
```

Classify findings by severity:

- **Blocker:** security, data loss, broken branch protection, failing required checks, unresolved merge conflict, or a clear production regression.
- **Major:** incorrect behavior, missing regression coverage, unsafe automation, broken API/contract, or incomplete migration.
- **Minor:** maintainability, test gaps with low immediate risk, documentation, or UX polish.
- **Informational:** observations that do not block merge.

Review repository-specific surfaces carefully: Python runtime and guardrails, persona/skill content, dashboard TypeScript, CI/security workflows, generated files, dependency changes, and secrets. Check whether tests cover changed behavior and whether the PR changes a canonical source without updating its documentation or dependents.

Produce one concise review record per PR containing: verdict, findings with file/line references, check state, mergeability, recommended action, and the exact command needed for follow-up. Do not approve or merge solely because a PR is old or small.

### 3. Check merge readiness

A PR is merge-ready only when all of these are true:

- It targets `main` and the head repository is expected.
- It is not a draft and is not blocked by review policy.
- Required checks are complete and green; check details are current.
- GitHub reports a clean merge state with no conflicts.
- No blocker or major finding remains.
- The change has appropriate tests and documentation.
- The user has authorized merging, unless an existing repository automation policy explicitly authorizes it.

When checks are pending, wait using a bounded polling loop or scheduled task rather than repeatedly hammering the API. If a check fails, inspect its logs and report the failure before retrying anything.

### 4. Merge safely

When explicitly authorized, merge through GitHub using the repository’s configured method. Prefer squash for focused changes and preserve the PR title/conventional commit format. Before merging, show the PR number, title, head/base branches, check summary, and merge method in the report. After merging, verify the merge commit on `origin/main` and confirm the PR is closed.

Never merge a draft, a conflicted PR, a PR with failing required checks, or a PR with unresolved blocker/major findings. Never close a PR merely to make the queue smaller.

### 5. Classify branch cleanup candidates

Use the repository’s existing `branch-cleanup.yml` logic as the authority for whether a branch is a no-op against the default branch. The key test is whether an in-memory merge would change the default branch tree, not merely whether the branch tip is an ancestor.

Before proposing deletion, exclude:

- `main`, the default branch, protected branches, and branches required by repository policy.
- Heads of open pull requests, including branches owned by this repository.
- Branches with conflicts or meaningful changes not merged elsewhere.
- Recently updated branches unless the user explicitly includes them.
- Any branch whose ownership or purpose is unclear.

Use dry-run classification first. For a deletion run, require explicit authorization and record the branch name, tip SHA, reason, and whether it was protected/open-PR excluded. Never delete unmerged branches just because they are old.

### 6. Report and verify

End with a dated report containing:

- Repository and default branch.
- PRs reviewed and verdicts.
- Checks pending/green/failed.
- Branches kept and why.
- Branches eligible for deletion and whether deletion was applied.
- Commands and GitHub URLs used.
- Remaining risks and next recommended action.

After any mutation, verify `git fetch --prune`, `git status --short --branch`, `git branch -a -vv`, the PR state, and the remote default branch. Leave the local worktree clean. Never present a local snapshot as live GitHub state.

## Reusable helper

Use `scripts/daily_pr_review.sh` for a deterministic inventory and dry-run branch report. It requires `gh`, `git`, `jq`, and authenticated access. Set `APPLY_DELETE=true` only after reviewing its output and receiving explicit authorization; the script still refuses default/protected/open-PR branches.

## Output contract

Return Markdown with one table for PR status and one table for branch cleanup. Include severity, evidence, and exact follow-up commands. Keep mutation separate from review so the daily run can safely be scheduled in dry-run mode.
