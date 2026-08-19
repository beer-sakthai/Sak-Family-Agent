---
name: SakSee-github-workspace-audit
description: Reconcile local workspace state, GitHub remote state, and agent memory/Supermemory   claims
  about repositories.
...
---

# GitHub Workspace Audit

## Overview

Run this skill when the user asks to check a repo on GitHub, audit the workspace, or “forget what you know and verify.” Its purpose is to produce a single source of truth by cross-checking:

1. **Actual GitHub repositories** accessible to the connected account.
2. **Local working copies** on disk and their git state.
3. **Agent memory / Supermemory claims** about which repos exist and where they live.

The output is a reconciliation report: verified repos, local checkouts, stale claims, and action items (uncommitted work, missing clones, memory updates).

## When to use

- User says “check repo in github” without naming one.
- User asks to audit, clean up, or reconcile workspace and memory.
- You are about to act on a repo name that came from memory but has not been verified this session.
- There are signs of duplicate local checkouts or renamed directories.

## Core workflow

### 1. Start a Composio session and confirm the GitHub connection

```python
COMPOSIO_SEARCH_TOOLS(
    queries=[{use_case: "list all repositories for GitHub user <owner>"}],
    session={generate_id: true}
)
```

Keep the returned `session_id` for all follow-up calls.

### 2. List real GitHub repos

Use the authenticated-user endpoint so private repos are included.

```python
COMPOSIO_MULTI_EXECUTE_TOOL(
    session_id="<session_id>",
    tools=[{
        "tool_slug": "GITHUB_LIST_REPOSITORIES_FOR_THE_AUTHENTICATED_USER",
        "arguments": {"per_page": 100, "sort": "updated", "direction": "desc"}
    }]
)
```

Record: `full_name`, `visibility`, `default_branch`, `pushed_at`, `updated_at`, `open_issues_count`, `homepage`, `html_url`.

### 3. Cross-check claimed repos in one batch

For every repo name from memory, Supermemory, or user mention, verify with `GITHUB_GET_A_REPOSITORY`. A 404 is a finding, not a tool failure.

```python
claimed = ["repo-a", "repo-b", "repo-c"]
tools = [{
    "tool_slug": "GITHUB_GET_A_REPOSITORY",
    "arguments": {"owner": "<owner>", "repo": name}
} for name in claimed]

COMPOSIO_MULTI_EXECUTE_TOOL(
    session_id="<session_id>",
    sync_response_to_workbench=True,
    tools=tools
)
```

### 4. Inspect local checkouts

On the local machine:

```bash
find /opt/data -maxdepth 2 -type d | sort

for d in /opt/data/<repo-a> /opt/data/<repo-b>; do
  if [ -d "$d/.git" ]; then
    echo "== $d =="
    git -C "$d" remote -v
    git -C "$d" branch -vv
    git -C "$d" status --short | head -40
  fi
done
```

Look for:
- Multiple directories pointing at the same remote.
- Uncommitted or untracked files.
- Missing expected checkouts.
- Directory names that no longer match memory.
- A claimed directory (e.g. `sak-family-agent-consolidated`) that does not exist on disk.

### 5. Check open issues and pull requests

For each verified repo:

```python
COMPOSIO_MULTI_EXECUTE_TOOL(
    session_id="<session_id>",
    tools=[
        {"tool_slug": "GITHUB_LIST_PULL_REQUESTS", "arguments": {"owner": "<owner>", "repo": "<repo>", "state": "open", "per_page": 100}},
        {"tool_slug": "GITHUB_LIST_REPOSITORY_ISSUES", "arguments": {"owner": "<owner>", "repo": "<repo>", "state": "open", "per_page": 100}}
    ]
)
```

Note: `GITHUB_LIST_REPOSITORY_ISSUES` may return PR-shaped entries. Filter by the presence of a `pull_request` field when you need true issues only.

### 6. Reconcile and report

Present findings in this order:
1. Verified GitHub repos (last push, visibility, open issues/PRs).
2. Local checkouts (path, remote, branch, cleanliness).
3. Stale memory/Supermemory claims (repos that 404 or have no local checkout).
4. Action items (commit, stash, clone, delete duplicate, update memory).

Do not push uncommitted changes without asking. Flag them and ask whether to commit, stash, or review.

### 7. Update durable memory

- Use `memory` or `supermemory_forget`/`supermemory_store` to remove stale repo claims.
- Add verified facts only for repos confirmed this session.
- Avoid recording transient timestamps unless the user explicitly needs them.

## Pitfalls

- **Trusting memory about repo existence.** Always verify with the GitHub API. Repos are deleted, renamed, or never created.
- **Using `gh` CLI when it may not be installed.** Prefer Composio tools; fall back to `curl` with `GITHUB_TOKEN` only if Composio is unavailable.
- **Raw `curl` to GitHub can be safety-blocked in this environment.** The terminal layer may time out or block direct HTTPS calls. If that happens, switch to Composio MCP tools instead of retrying the same curl.
- **The `.env` token may not be a git PAT.** In this workspace, `GITHUB_TOKEN` from `/opt/data/.env` is not accepted for `git push`. Commit locally and report the push failure if no real PAT/SSH key is available.
- **GitHub raw content may return a pre-signed S3 URL, not inline text.** `GITHUB_GET_RAW_REPOSITORY_CONTENT` often responds with `data.content.s3url`. Fetch that URL separately to get the file body. Do not log or share the S3 URL — it carries sensitive query parameters.
- **Directory listings can include stale or phantom entries.** A `GITHUB_GET_REPOSITORY_CONTENT` directory response may list files that return 404 on direct fetch (caching, case drift, deleted-but-listed paths). Verify critical paths individually before treating them as facts.
- **One local directory per remote assumption.** The same remote can be cloned into multiple directories with different states.
- **Treating 404 as failure.** `GITHUB_GET_A_REPOSITORY` 404 means the repo name is stale — record it.
- **Ignoring dirty working trees.** Uncommitted work is usually the real state the user cares about.
- **Credential exposure.** Never print `.env` contents, tokens, or full API responses. Summarize only.

## Environment-specific reference

See `references/environment-specific-notes.md` for concrete details about this workspace: missing `gh`, blocked raw curl, `.env` token behavior, and the Composio-first workflow.

## Reference

See `references/session-audit-example.md` for a concrete transcript from a real workspace reconciliation, including how stale Supermemory claims were detected and how duplicate local checkouts were surfaced.

See `references/deep-repo-inspection-pattern.md` for a pattern to inspect an unfamiliar repository after the workspace-level reconciliation is done — useful when the user says “it’s your project now, check what it needs.”

See `references/identity-mismatch-and-repo-takeover.md` for identity-file mismatch checks and a deep repo takeover example (`Food-Penguin-Limited`, 2026-07-06).

## Identity-file mismatch check

When the user asks whether the agent's SOUL.md was updated today, or wants to edit the agent persona, check whether the SOUL.md path the system prompt claims as authoritative actually contains the current agent's persona. In this workspace `/opt/data/SOUL.md` is SakKing's persona even though it is loaded for SakSee; the proper Saksee files live under `/opt/data/personas/saksee/SOUL.md`, `/opt/data/profiles/saksee/SOUL.md`, and the repo copy in `Sak-Family-Agent/personas/saksee/SOUL.md`. Do not overwrite another sibling's SOUL.md when updating your own. Update all known Saksee copies to keep them consistent.
