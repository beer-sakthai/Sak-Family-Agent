# HF Hub Discussions API Reference

Comprehensive reference for the Hugging Face Hub Discussions and Pull Requests API — both the Python `huggingface_hub` library and the underlying REST endpoints.

---

## Overview

The HF Hub Discussions API lets you programmatically manage discussions and pull requests on any model, dataset, or Space repository. It supports creating, reading, commenting, renaming, status changes, and merging.

**Two interaction modes:**
1. **`huggingface_hub` Python library** (`HfApi`) — high-level wrapper
2. **REST API** — direct HTTP calls to `https://huggingface.co/api/<repo_type>s/<repo_id>/discussions`

---

## Python API (`huggingface_hub`)

All methods are on `HfApi`. Use a single instance:

```python
from huggingface_hub import HfApi
api = HfApi()
```

### List Discussions

```python
def get_repo_discussions(
    repo_id: str,
    *,
    author: str | None = None,
    discussion_type: str | None = None,   # "pull_request", "discussion", "all"
    discussion_status: str | None = None,  # "open", "closed", "all"
    repo_type: str | None = None,          # None="model", "dataset", "space"
    token: bool | str | None = None,
) -> Iterator[Discussion]:
```

Returns an iterator of `Discussion` objects (lightweight — title, num, author, status, created_at, is_pull_request).

**Examples:**
```python
# All discussions on a model
discs = list(api.get_repo_discussions("bert-base-uncased"))

# Only open pull requests on a dataset
prs = list(api.get_repo_discussions(
    "bigcode/the-stack",
    discussion_type="pull_request",
    discussion_status="open",
    repo_type="dataset"
))

# Filter by author
mine = list(api.get_repo_discussions(
    "username/my-model",
    author="username"
))
```

Pagination is handled automatically — the method yields one discussion at a time across pages.

### Get Discussion Details

```python
def get_discussion_details(
    repo_id: str,
    discussion_num: int,
    *,
    repo_type: str | None = None,
    token: bool | str | None = None,
) -> DiscussionWithDetails:
```

Returns full details including all events (comments, status changes, title changes), diff (for PRs), merge status, and conflicting files.

**Key fields on `DiscussionWithDetails`:**
| Field | Type | Description |
|-------|------|-------------|
| `title` | str | Discussion title |
| `num` | int | Discussion number |
| `status` | str | "open" or "closed" |
| `is_pull_request` | bool | Whether it's a PR |
| `events` | list[DiscussionEvent] | Timeline of all events |
| `diff` | str or None | Unified diff (PRs only) |
| `conflicting_files` | list or None | Files with merge conflicts (PRs only) |
| `target_branch` | str or None | Base branch for PR |
| `merge_commit_oid` | str or None | Merge commit hash (merged PRs) |

**Example:**
```python
details = api.get_discussion_details(
    "username/my-model", 42
)
for event in details.events:
    print(event.type, event.created_at)
```

### Create Discussion

```python
def create_discussion(
    repo_id: str,
    title: str,
    *,
    description: str | None = None,
    pull_request: bool = False,
    repo_type: str | None = None,
    token: bool | str | None = None,
) -> DiscussionWithDetails:
```

- `title`: 3–200 characters, stripped of leading/trailing whitespace
- `description`: defaults to generic message if not provided
- `pull_request=True`: creates a **draft PR** (not yet ready to merge)

**Example:**
```python
disc = api.create_discussion(
    "username/my-model",
    title="Add training script",
    description="This PR adds the training script used for fine-tuning.",
    pull_request=True,
)
print(f"Created discussion #{disc.num}")
```

### Create Pull Request (wrapper)

```python
def create_pull_request(
    repo_id: str,
    title: str,
    *,
    description: str | None = None,
    repo_type: str | None = None,
    token: bool | str | None = None,
) -> DiscussionWithDetails:
```

Equivalent to `create_discussion(pull_request=True)`. Created PRs start in `"draft"` status.

### Comment on Discussion

```python
def comment_discussion(
    repo_id: str,
    discussion_num: int,
    comment: str,
    *,
    repo_type: str | None = None,
    token: bool | str | None = None,
) -> DiscussionComment:
```

Comments support **markdown** formatting including:
- `@username` mentions
- `**bold**`, `*italic*`, `~strikethrough~`
- `[links](url)`
- Headers, lists, code blocks

**Example:**
```python
api.comment_discussion(
    "username/my-model", 42,
    "Thanks for the contribution! **Looks good to me.**"
)
```

### Rename Discussion

```python
def rename_discussion(
    repo_id: str,
    discussion_num: int,
    new_title: str,
    *,
    repo_type: str | None = None,
    token: bool | str | None = None,
) -> DiscussionTitleChange:
```

### Change Status (Open/Close)

```python
def change_discussion_status(
    repo_id: str,
    discussion_num: int,
    new_status: Literal["open", "closed"],
    *,
    comment: str | None = None,
    repo_type: str | None = None,
    token: bool | str | None = None,
) -> DiscussionStatusChange:
```

**Example:**
```python
api.change_discussion_status(
    "username/my-model", 42,
    "closed",
    comment="Resolved in v2.0"
)
```

### Merge Pull Request

```python
def merge_pull_request(
    repo_id: str,
    discussion_num: int,
    *,
    comment: str | None = None,
    repo_type: str | None = None,
    token: bool | str | None = None,
):
```

Merges a PR. The PR must have no conflicts and must have been moved from `"draft"` to `"open"`.

### Edit Comment

```python
def edit_discussion_comment(
    repo_id: str,
    discussion_num: int,
    comment_id: str,
    new_content: str,
    *,
    repo_type: str | None = None,
    token: bool | str | None = None,
) -> DiscussionComment:
```

Requires the `comment_id` (32-char hex string, obtained from `DiscussionComment.id`).

### Hide Comment (Irreversible)

```python
def hide_discussion_comment(
    repo_id: str,
    discussion_num: int,
    comment_id: str,
    *,
    repo_type: str | None = None,
    token: bool | str | None = None,
) -> DiscussionComment:
```

⚠ **Warning:** This is irreversible. Hidden comment content cannot be retrieved.

---

## REST API (Direct HTTP)

Base URL: `https://huggingface.co/api`

### List Discussions

```
GET /api/{repo_type}s/{repo_id}/discussions
```

**Query params:** `type` (discussion/pull_request/all), `status` (open/closed/all), `author`, `p` (page, 0-indexed)

**Response:**
```json
{
  "count": 42,
  "start": 0,
  "discussions": [
    {
      "title": "My Discussion",
      "num": 1,
      "status": "open",
      "createdAt": "2024-01-01T00:00:00.000Z",
      "author": {"name": "username"},
      "isPullRequest": false,
      "repo": {"name": "username/repo", "type": "model"}
    }
  ]
}
```

### Get Discussion Details

```
GET /api/{repo_type}s/{repo_id}/discussions/{num}?diff=1
```

The `diff=1` param includes the unified diff in the response.

### Create Discussion

```
POST /api/{repo_type}s/{repo_id}/discussions
```

**Body:**
```json
{
  "title": "Discussion title",
  "description": "Optional description",
  "pullRequest": false
}
```

### Add Comment

```
POST /api/{repo_type}s/{repo_id}/discussions/{num}/comment
```

**Body:** `{"comment": "Markdown comment text"}`

### Change Title

```
POST /api/{repo_type}s/{repo_id}/discussions/{num}/title
```

**Body:** `{"title": "New title"}`

### Change Status

```
POST /api/{repo_type}s/{repo_id}/discussions/{num}/status
```

**Body:** `{"status": "open"}` or `{"status": "closed"}`

Optional: `{"status": "closed", "comment": "Closing comment"}`

### Merge PR

```
POST /api/{repo_type}s/{repo_id}/discussions/{num}/merge
```

**Body:** `{"comment": "Optional merge comment"}`

### Edit Comment

```
POST /api/{repo_type}s/{repo_id}/discussions/{num}/comment/{comment_id}/edit
```

**Body:** `{"content": "Updated markdown content"}`

---

## Authentication

All write operations require authentication. Two methods:

1. **Token from environment** (recommended):
   ```python
   # Token loaded via `huggingface_hub` login or `HF_TOKEN` env var
   api = HfApi()  # automatically uses saved token
   ```

2. **Pass token explicitly**:
   ```python
   api = HfApi(token="hf_your_token_here")
   # Or per-call
   api.create_discussion("user/repo", "Title", token="hf_token")
   ```

For REST API, pass token as `Authorization: Bearer hf_...` header.

---

## Common Patterns

### Automate PR Review Workflow

```python
def review_and_merge(repo_id: str, pr_num: int):
    """Fetch PR details, post review comment, then merge."""
    api = HfApi()
    details = api.get_discussion_details(repo_id, pr_num)

    if details.conflicting_files:
        api.comment_discussion(
            repo_id, pr_num,
            f"❌ Merge conflict in {', '.join(details.conflicting_files)}"
        )
        return False

    api.comment_discussion(
        repo_id, pr_num,
        "✅ Changes look good! Merging now."
    )
    api.merge_pull_request(repo_id, pr_num)
    return True
```

### Create PR with Auto-Close Stale Issues

```python
def create_fix_pr(repo_id: str, fix_branch: str, issue_num: int):
    api = HfApi()

    # Create PR
    pr = api.create_pull_request(
        repo_id,
        title=f"Fix issue #{issue_num}",
        description=f"Resolves #{issue_num}. See branch: {fix_branch}"
    )

    # Add cross-reference to the issue discussion
    api.comment_discussion(
        repo_id, issue_num,
        f"Fix submitted in PR #{pr.num}"
    )

    return pr.num
```

---

## Best Practices & Pitfalls

| Pitfall | Solution |
|---------|----------|
| PRs created programmatically start as **draft** | Must be manually moved to "open" before merging |
| Title max length is **200 characters** | Keep titles concise |
| Discussion numbers are **per-repo** integers | Track `repo_id + num` as composite key |
| `hide_discussion_comment` is **irreversible** | Warn before using programmatically |
| Pagination is 0-indexed (`p=0`, `p=1`, ...) | Use iterator in Python; track page manually in REST |
| Comments support **full markdown** | Sanitize user-generated content to prevent XSS |

---

## Data Models

| Class | Key Fields | Returned By |
|-------|-----------|-------------|
| `Discussion` | `title, num, author, status, created_at, is_pull_request` | `get_repo_discussions` |
| `DiscussionWithDetails` | `+ events, diff, conflicting_files, target_branch, merge_commit_oid` | `get_discussion_details`, `create_discussion` |
| `DiscussionComment` | `id, type, created_at, author, content, edited, hidden` | `comment_discussion`, `edit_discussion_comment` |
| `DiscussionStatusChange` | `id, type, created_at, author, new_status, comment` | `change_discussion_status` |
| `DiscussionTitleChange` | `id, type, created_at, author, old_title, new_title` | `rename_discussion` |

---

**Sources:**
- `huggingface_hub` source code (`hf_api.py` lines 7215–7950)
- HF Hub API docs: https://huggingface.co/docs/huggingface_hub/main/package_reference/hf_api#discussions
- HF Hub discussions guide: https://huggingface.co/docs/hub/en/discussions
