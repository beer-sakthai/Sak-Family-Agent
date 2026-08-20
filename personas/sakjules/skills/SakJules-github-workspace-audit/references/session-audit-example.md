# Real Session — Workspace Repo Audit Example

This reference captures the exact signals, commands, and reconciliations from a live audit so future runs can reuse the pattern.

## Trigger

User said: “are you ready for your first project” → “check repo in github” → “delete about what you know in workspace and what is we have remember check and audit.”

Translation: forget assumptions; verify actual GitHub repos and local workspace; reconcile with memory.

## What memory claimed

- `sak-family-agent-consolidated/` was the only working copy of `beer-sakthai/Sak-Family-Agent`.
- House of Sak local checkout was at `/opt/data/house-of-sak-report`.
- `beer-sakthai/saksee-skills`, `beer-sakthai/saksit-skills`, `beer-sakthai/sakthai-agent-v2`, `beer-sakthai/SakThai-Agent`, and `beer-sakthai/sakthai-skills` existed as canonical skills repos.
- `gh` CLI + raw `curl` were the normal path for GitHub checks.

## What verification revealed

### GitHub repos that actually exist under `beer-sakthai`

| Repo | Visibility | Default | Last push (UTC) | Open issues | Open PRs |
|------|------------|---------|-----------------|-------------|----------|
| `beer-sakthai/Sak-Family-Agent` | public | `main` | 2026-07-06 07:39:39 | 0 | 0 |
| `beer-sakthai/house-of-sak` | public | `main` | 2026-07-06 07:39:27 | 0 | 0 |
| `beer-sakthai/Food-Penguin-Limited` | private | `main` | 2026-07-02 14:04:44 | 0 | 0 |

### Local checkouts

| Local path | Remote | Branch | State |
|------------|--------|--------|-------|
| `/opt/data/Sak-Family-Agent` | `https://github.com/beer-sakthai/Sak-Family-Agent.git` | `main` | clean |
| `/opt/data/house-of-sak` | `https://github.com/beer-sakthai/house-of-sak.git` | `main` | clean |
| `/opt/data/house-of-sak-report` | same remote as `house-of-sak` | `main` | **dirty**: modified `PLAN.md`, `index.html`; many untracked reports/files |

### Stale claims

The following repos returned 404 on GitHub and had no local checkout:
- `beer-sakthai/saksee-skills`
- `beer-sakthai/saksit-skills`
- `beer-sakthai/sakthai-agent-v2`
- `beer-sakthai/SakThai-Agent`
- `beer-sakthai/sakthai-skills`

Also, `/opt/data/sak-family-agent-consolidated/` did **not** exist on disk; the live checkout is `/opt/data/Sak-Family-Agent/`.

## Tools used

1. `COMPOSIO_SEARCH_TOOLS` with `generate_id: true` to establish session and confirm GitHub connection.
2. `GITHUB_LIST_REPOSITORIES_FOR_THE_AUTHENTICATED_USER` to enumerate real repos.
3. `GITHUB_GET_A_REPOSITORY` batch call to verify claimed repo names.
4. `GITHUB_LIST_PULL_REQUESTS` + `GITHUB_LIST_REPOSITORY_ISSUES` for each verified repo.
5. Local `find`, `git remote -v`, `git branch -vv`, `git status --short` for disk state.
6. `supermemory_search` and `cronjob list` to gather memory/cron claims.

## Key decisions

- Did **not** push the dirty `house-of-sak-report/` tree without user approval.
- Did **not** update memory with unverified repo names.
- Used Composio tools instead of `gh` because `gh` was not installed and raw `curl` timed out and triggered the safety blocker.

## Follow-up actions offered to user

1. Commit/push the uncommitted `house-of-sak-report/` changes after review.
2. Clean stale Supermemory entries about non-existent repos.
3. Decide whether to remove duplicate `house-of-sak` local checkout or rename/merge it with `house-of-sak-report`.

## Lessons embedded in the skill

- Verify before trusting memory about repo existence.
- Check both GitHub API and local disk; neither alone is enough.
- A dirty local checkout is usually the most important finding.
- Use Composio GitHub tools when `gh` is unavailable.
- 404s are data, not failures.
