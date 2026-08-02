# Composio GitHub Tools — Repo Management & Multi-File Commit

Use Composio's MCP-integrated GitHub tools as an alternative to `gh` CLI or raw `curl` API calls. The key difference: tools are called via `COMPOSIO_MULTI_EXECUTE_TOOL` (batch) or `COMPOSIO_REMOTE_WORKBENCH` (scripted) rather than terminal commands.

## Prerequisites

- GitHub already connected in Composio (check with `COMPOSIO_SEARCH_TOOLS`)
- Active session ID from `COMPOSIO_SEARCH_TOOLS` (pass `session_id` in all follow-up calls)

## Key Tools

| Tool Slug | Purpose |
|-----------|---------|
| `GITHUB_GET_A_REPOSITORY` | Check if repo exists (200 = exists, 404 = not found) |
| `GITHUB_CREATE_A_REPOSITORY_FOR_THE_AUTHENTICATED_USER` | Create new repo under the connected user |
| `GITHUB_LIST_BRANCHES` | List branches, find default branch name |
| `GITHUB_GET_A_BRANCH` | Get branch details including HEAD commit SHA |
| `GITHUB_COMMIT_MULTIPLE_FILES` | Atomic multi-file commit (create/update/delete) |
| `GITHUB_GET_REPOSITORY_CONTENT` | Read file content from a repo |
| `GITHUB_CREATE_OR_UPDATE_FILE_CONTENTS` | Single file create/update (fallback if multi-file fails) |

## Workflow: Create Repo + Push Multiple Files

### Step 1: Discover tools and establish session

```python
# First call — always generate a new session ID
COMPOSIO_SEARCH_TOOLS(
    queries=[{use_case: "create a GitHub repository for the authenticated user"}],
    session={generate_id: true}
)
# → returns session_id to reuse in all subsequent calls
```

### Step 2: Check if repo exists

```python
COMPOSIO_MULTI_EXECUTE_TOOL(
    session_id="<session_id>",
    sync_response_to_workbench=true,
    tools=[{
        tool_slug: "GITHUB_GET_A_REPOSITORY",
        arguments: {owner: "username", repo: "repo-name"}
    }]
)
# 200 → exists, 404 → does not exist
```

### Step 3: Create repo (if needed)

```python
COMPOSIO_MULTI_EXECUTE_TOOL(
    session_id="<session_id>",
    tools=[{
        tool_slug: "GITHUB_CREATE_A_REPOSITORY_FOR_THE_AUTHENTICATED_USER",
        arguments: {
            name: "repo-name",
            private: false,
            auto_init: true,
            description: "Optional description"
        }
    }]
)
# Returns default_branch from the response (usually "main")
```

### Step 4: Prepare files for commit

Read local files using `read_file` or `terminal`, then construct the upserts array.

**Text files** — read with `read_file` and pass as `encoding: "utf-8"`:

```python
upserts = []
# Use content from read_file output (strip the "1|" line number prefix if present)
upserts.append({
    path: "path/in/repo/file.md",
    content: file_content_string,
    encoding: "utf-8"
})
```

**Binary files (PNG, images, etc.)** — base64 encode first:

```bash
base64 -w0 /path/to/image.png > /tmp/image.b64
```

Then read the base64 file and pass as `encoding: "base64"`:

```python
upserts.append({
    path: "path/in/repo/image.png",
    content: base64_string,
    encoding: "base64"
})
```

### ⚠️ Critical Pitfall: Remote Workbench Can't See Local Files

`COMPOSIO_REMOTE_WORKBENCH` runs in a **remote sandbox** — paths like `/opt/data/...` do not exist there. Do NOT try to read local files from within the workbench.

**Do this instead:**
- Read files locally using `read_file` or `terminal`
- Pass the content inline to `COMPOSIO_MULTI_EXECUTE_TOOL`
- OR use `terminal` on the local machine to construct the full JSON payload, then save it and pass it

The multi-execute tool handles large inline payloads. A 122K-character commit (15 files including a 65K base64 PNG) worked inline with no issues.

### Step 5: Atomic multi-file commit

```python
COMPOSIO_MULTI_EXECUTE_TOOL(
    session_id="<session_id>",
    tools=[{
        tool_slug: "GITHUB_COMMIT_MULTIPLE_FILES",
        arguments: {
            owner: "username",
            repo: "repo-name",
            branch: "main",  # use the default_branch from create response
            message: "📂 Commit message with emoji",
            upserts: upserts_array,
            deletes: []  # list of file paths to delete
        }
    }]
)
```

The response includes:
- `new_commit_sha` — the commit hash
- `commit.html_url` — direct link to the commit on GitHub
- `path_status` — array showing blob_sha and operation per file
- `branch_created` — boolean indicating if a new branch was created

### Step 6: Verify

```python
COMPOSIO_MULTI_EXECUTE_TOOL(
    session_id="<session_id>",
    tools=[{
        tool_slug: "GITHUB_GET_A_REPOSITORY",
        arguments: {owner: "username", repo: "repo-name"}
    }]
)
# Check pushed_at, language detection, etc.
```

## Pitfalls

1. **Workbench ≠ local filesystem**: `COMPOSIO_REMOTE_WORKBENCH` cannot access `/opt/data/`, `~/`, or any local path. Prepare all data on the local machine first.

2. **GITHUB_COMMIT_MULTIPLE_FILES requires ≥1 upsert or delete**: An empty commit (both upserts and deletes empty) will be rejected with a 422 validation error.

3. **Binary encoding**: For non-text files (PNG, PDF, etc.), you MUST set `encoding: "base64"` and provide a base64-encoded string. Text files default to `encoding: "utf-8"`.

4. **New branch creation**: When committing to a branch that doesn't exist yet, you MUST provide `base_branch: "main"` to create it from. If the branch already exists (like `main` after repo creation with `auto_init`), `base_branch` is not needed.

5. **Session management**: Always pass the `session_id` returned by `COMPOSIO_SEARCH_TOOLS` in all subsequent meta-tool calls. Without it, the workflow state is lost.

6. **Commit message encoding**: Emoji characters (📂, 🚀, etc.) work fine in commit messages through the Composio tools.

7. **Batch splitting for large payloads**: If a single `GITHUB_COMMIT_MULTIPLE_FILES` call with ALL files fails (422, timeout, or unexpected errors), split the files into smaller batches:
   - Text files only: ~57KB of content + JSON overhead works in one call
   - PNG base64 (~65KB) can be committed separately as a second commit
   - Split by natural groups: origin stories batch, business docs batch, media batch
   - Each batch gets its own commit message with part numbering (e.g. "part 1/3")

8. **Inline payload vs workbench**: For multi-file commits, use `COMPOSIO_MULTI_EXECUTE_TOOL` directly with inline upserts — the inline JSON payload handles 120K+ characters reliably. Only use the remote workbench when you need programmed pagination, looping, or bulk tool calls that cannot be done inline.

## Example: Full Cycle (from the session)

```
Step 1: COMPOSIO_SEARCH_TOOLS with generate_id → session "bank"
Step 2: GITHUB_GET_A_REPOSITORY(beer-sakthai, house-of-sak) → 404
Step 3: GITHUB_CREATE_A_REPOSITORY_FOR_THE_AUTHENTICATED_USER → created, default_branch: main
Step 4: Read 14 text files via read_file + base64 encode ig-card.png via terminal
Step 5: GITHUB_COMMIT_MULTIPLE_FILES → 15 files in one commit, commit SHA returned
Step 6: GITHUB_GET_A_REPOSITORY → verified, pushed_at updated
```

## Related Tools

For file-by-file operations (single file create/update):
- `GITHUB_CREATE_OR_UPDATE_FILE_CONTENTS` — requires `sha` for updates to prevent clobbering

For reading existing repo files:
- `GITHUB_GET_REPOSITORY_CONTENT` — returns base64-encoded file content (decode with `base64.b64decode()`)