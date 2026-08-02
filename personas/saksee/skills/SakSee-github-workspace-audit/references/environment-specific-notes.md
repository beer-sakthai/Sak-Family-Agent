## Environment-specific GitHub workflow notes

Captured from a 2026-07-06 workspace audit on the saksee profile.

### What is special about this environment

- The `gh` CLI is **not installed** (`gh: command not found`).
- Raw `curl` to `https://api.github.com` may be **safety-blocked / timed out by the terminal layer** even with a `GITHUB_TOKEN` from `.env`.
- The `GITHUB_TOKEN` value stored in `/opt/data/.env` is **not a valid GitHub PAT for git operations**; embedding it into `https://oauth2:${TOKEN}@github.com/...` for `git push` returns `Invalid username or token. Password authentication is not supported for Git operations.`
- **Composio has an active GitHub connection** for `beer-sakthai`. Prefer Composio MCP tools (`COMPOSIO_SEARCH_TOOLS` → `COMPOSIO_MULTI_EXECUTE_TOOL` with `GITHUB_LIST_REPOSITORIES_FOR_THE_AUTHENTICATED_USER`, `GITHUB_GET_A_REPOSITORY`, etc.) for all GitHub reads and writes.
- The `lsof` command is **not installed** on this system, requiring alternative methods for checking port usage and process information.

### Verified workflow for listing + cross-checking repos

1. `COMPOSIO_SEARCH_TOOLS` with `generate_id: true` to start a session.
2. `GITHUB_LIST_REPOSITORIES_FOR_THE_AUTHENTICATED_USER` to get real repos (includes private).
3. `GITHUB_GET_A_REPOSITORY` in a batch for every repo name that memory/Supermemory claims exists. Treat 404 as a verified finding that the claim is stale.
4. Local inspection via `find` + `git -C <path> remote/branch/status`.
5. If a `git push` is needed and no PAT/SSH is available, commit locally and report the push failure instead of trying credential workarounds.

### Alternative methods for process and port investigation

When `lsof` is not available, use these alternative commands for investigating processes and port usage:

```bash
# Check which process is using a port (if netstat is available)
netstat -tulpn | grep :3001

# Check process information directly
ps aux | grep sakthai

# Get detailed information about a specific process
ps -p <pid> -o pid,ppid,cmd

# Check for processes by pattern
pgrep -f "sakthai dashboard"
```

### Restoring remote URL after a token-based push attempt

If you temporarily set the origin to `https://oauth2:${TOKEN}@github.com/owner/repo.git`, restore the clean public URL immediately after push failure or success:

```bash
git remote set-url origin https://github.com/owner/repo.git
git remote -v
```

This prevents credential artifacts from lingering in `.git/config`.

### Memory/Supermemory cleanup

When the audit shows repos claimed in memory are 404 on GitHub:
- Use `supermemory_forget` for stale Supermemory entries (if credits available).
- Use `memory` operations to replace stale local entries; memory may be near full, so remove old contradictory entries in the same batch before adding corrected facts.
- Do not add new memory entries with raw timestamps unless the user needs them; focus on durable structural facts.
