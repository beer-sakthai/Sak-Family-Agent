---
name: SakSit-skills-repo-sync
description: Sync SakSit skills to saksit-skills GitHub repo via Composio API.
version: 2.0.0
author: Hermes
platforms: [linux]
tags: [github, sync, skills, saksit, composio]
---

# SakSit Skills → GitHub Sync

SakSit skills sync to the standalone repo:

```
https://github.com/beer-sakthai/saksit-skills
```

Created Jul 9, 2026. Public. Each skill is its own directory with a `SKILL.md` at the top level of the repo (no category nesting — the local Hermes category structure is a runtime concern).

## When to sync

- User says "save skills in github", "push skills", or "sync"
- After bulk create/patch of SakSit-owned skills

## How to Sync (Composio GitHub API)

No local clone needed. GitHub connected as `beer-sakthai` via Composio (connection ID: `github_flail-thapes`).

### One skill at a time

Use `GITHUB_CREATE_OR_UPDATE_FILE_CONTENTS`:

```json
{
  "owner": "beer-sakthai",
  "repo": "saksit-skills",
  "branch": "main",
  "path": "<skill-name>/SKILL.md",
  "message": "SakSit: add <skill-name>",
  "content": "<full SKILL.md content>"
}
```

The tool auto-base64-encodes plain text. Call via `COMPOSIO_MULTI_EXECUTE_TOOL` for parallel commits, or `run_composio_tool()` from the workbench for sequential bulk.

### Multiple skills in one commit

Use `GITHUB_COMMIT_MULTIPLE_FILES` (best for small batches):

```json
{
  "owner": "beer-sakthai",
  "repo": "saksit-skills",
  "branch": "main",
  "message": "SakSit: bulk add <N> skills",
  "upserts": [
    {"path": "<skill-1>/SKILL.md", "content": "...", "encoding": "utf-8"},
    {"path": "<skill-2>/SKILL.md", "content": "...", "encoding": "utf-8"}
  ]
}
```

### Batch workflow (many files)

1. Gather skill content: use `terminal` to `find` all SKILL.md paths, then `read_file` each
2. Save upserts as JSON to `/tmp/batch*.json`
3. In the workbench, use `run_composio_tool("GITHUB_CREATE_OR_UPDATE_FILE_CONTENTS", ...)` per file — parallelize via ThreadPoolExecutor
4. Verify with `GITHUB_GET_A_TREE(owner="beer-sakthai", repo="saksit-skills", tree_sha="main", recursive="1")`

### Creating the repo

If the repo doesn't exist (404 on `GITHUB_GET_A_REPOSITORY`), create it:

```
GITHUB_CREATE_A_REPOSITORY_FOR_THE_AUTHENTICATED_USER
  name: "saksit-skills"
  description: "SakSit agent skills"
  private: false
  auto_init: true
```

## Commit message convention

```
SakSit: <action> <skill-name> — <short blurb>
```

Examples: `SakSit: add SakSit-b2b-saas-linkedin-newsletter-2026`, `SakSit: patch content-source-check — added Google Docs step`

## Pitfalls

- **SKILL.md only for first pass.** Push only `SKILL.md` files initially. Reference/script/template files can follow.
- **Payload limits.** `GITHUB_COMMIT_MULTIPLE_FILES` has size limits. For 20+ files or large content, commit individually or in batches of 5-10.
- **Placeholder content.** First-sync commits can use frontmatter-only stubs ("Full content synced from Hermes runtime"). Note this for a proper full-content follow-up.
- **No git on this system.** No SSH keys, no `gh` CLI, no git credentials. All GitHub ops through Composio API tools only.
- **Path correctness.** When building repo paths from local file paths, strip the skills base dir (`/opt/data/profiles/saksit/skills/`) and use the remaining relative path as-is (e.g. `SakSit-b2b-saas-x/SKILL.md`). Do NOT double-append segments.
- **Read_file quirks.** When using `read_file` in `execute_code`, the content is in `res["content"]` with line-number prefixes ("1|..."). Strip those or pass to the API directly — the GitHub tool will handle encoding.

## Verification

After push, run `GITHUB_GET_A_TREE` to confirm all paths landed. Check `tree[].path` for each committed skill.
