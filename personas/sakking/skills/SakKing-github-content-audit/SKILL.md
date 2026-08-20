---
name: SakKing-github-content-audit
description: Read GitHub repository files, audit directory structures, and extract    file contents
  via the GitHub Contents API u2014 especially useful when CLI/terminal    tools are
  unavailable and youre operating through an API gateway (Composio, MCP,    etc.).
...
---

# GitHub Content Audit

Read, decode, and traverse GitHub repository files via the GitHub Contents API and Git Trees API. Designed for environments where direct git/CLI access isn't available (Composio gateway, MCP proxy, Hermes without terminal tools).

## When to use

- You need to inspect a repo's structure but don't have `git`, `gh`, or a local clone
- Auditing which files exist for each agent/persona in a monorepo
- Reading specific files (SOUL.md, configs, SKILL.md, README.md) from GitHub without downloading the whole repo
- Generating a handoff report of what files need automation or versioning
- Operating through Composio's `proxy_execute` or similar API gateway

## Prerequisites

- GitHub authentication token with `repo` scope (for private repos) or public access
- In Composio: the `github` toolkit must have an active connection

## Core Techniques

### 1. List directory contents

```bash
# Via curl (general)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/contents/$PATH?ref=$BRANCH"
```

The API returns an **array** for directories, **single object** for files. Always check `type` field.

### 2. Read and decode a file

GitHub encodes file content in base64. Decode it:

```python
import base64, json
# From API response
content_b64 = data['content']
decoded = base64.b64decode(content_b64).decode('utf-8')
```

If using Python (Composio workbench, execute_code), this is straightforward. In shell:

```bash
curl -s ... | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
print(base64.b64decode(data['content']).decode('utf-8'))
"
```

### 3. Get the full repo tree (recursive)

For auditing an entire monorepo structure without walking each directory:

```bash
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/git/trees/$BRANCH?recursive=1"
```

This returns every file and directory in one call. Filter by path or type client-side.

### 4. Batch multiple files

Since file reads are independent, batch them when possible — use parallel requests (ThreadPoolExecutor in workbench, or parallel curl) to avoid sequential round-trips.

## Common Audit Patterns

### Audit per-agent persona files

For a monorepo with agent personas under `personas/<agent_name>/`:

```python
import requests, base64, json

api = "https://api.github.com/repos/owner/repo"
branch = "main"
agents = ["agent1", "agent2", "agent3"]

for agent in agents:
    r = requests.get(f"{api}/contents/personas/{agent}/SOUL.md?ref={branch}")
    if r.ok:
        content = base64.b64decode(r.json()['content']).decode()
        # Extract first line (identity) and size
        first_line = content.split('\n')[0]
        print(f"{agent}: {r.json()['size']}b — {first_line[:80]}")
    else:
        print(f"{agent}: MISSING (HTTP {r.status_code})")
```

### Check env templates for all agents

```python
r = requests.get(f"{api}/contents/infra/vm-agents/env-templates?ref={branch}")
for item in r.json():
    print(f"  {item['name']} ({item['size']}b)")
```

### Find all files of a type

```python
r = requests.get(f"{api}/git/trees/{branch}?recursive=1")
tree = r.json()['tree']
soul_files = [f for f in tree if f['path'].endswith('SOUL.md')]
for f in soul_files:
    print(f"  {f['path']}")
```

## Output Format — Handoff Report

When generating a handoff for another agent (e.g., SakJules for CI/CD), produce a structured report:

```
## Handoff: [Target Agent]

### Files Needing Automation
| Category | File | Status | Action Needed |
|----------|------|--------|---------------|

### Infrastructure
- Deployment scripts
- Systemd units
- Env templates

### CI/CD
- Workflow files
- Pipeline definitions

### Missing / Pending
- What doesn't exist yet
- What needs creation
```

## Pitfalls

- **Base64 padding:** GitHub's `content` field includes `\n` every 76 chars — Python's `base64.b64decode()` handles this fine, but shell tools may need `tr -d '\n'` first.
- **Rate limits:** 5000/hr authenticated, 60/hr unauthenticated. For large audits, batch and paginate.
- **Large files (>1MB):** The Contents API returns a blob SHA instead of inlined content. Fall back to `git/blobs/{sha}` to fetch large files.
- **404 means gone:** A 404 from `/{owner}/{repo}/contents/path` means either the file doesn't exist or the repo itself doesn't exist. Use `GET /repos/{owner}/{repo}` first to verify the repo exists.
- **Directory vs file responses:** Directories return a JSON array `[]`, files return a single JSON object `{}`. Your code must handle both — check `isinstance(data, list)` or `data.get('type')`.
- **Composio proxy_execute note:** When using `proxy_execute("GET", "/repos/o/r/contents/path", "github")`, the response wraps in `result.get("data", {}).get("results", [])` — the actual API response is deeper than a direct curl call. Log keys to discover the right path.

## Session References

See `references/sak-family-audit-2026-07-04.md` for a concrete example of auditing a 6-agent family monorepo.
