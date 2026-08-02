# HF Learnings Log — Pull Requests & Discussions

## 2026-07-24: hf-hub-pull-requests-and-discussions-api — Complete Deep Dive (Topic #123)

### Summary
Comprehensive deep-dive into Hugging Face Hub's Pull Requests and Discussions API. Covers the full lifecycle — creating, reading, commenting, editing, merging, and closing discussions/PRs using the `huggingface_hub` Python SDK (v1.24.0) and the underlying git ref architecture. This topic was previously tracked but had no learning content written; this fills the gap with authoritative source-verified documentation.

### Architecture — How Hub PRs Actually Work

The Hub's PR system is intentionally different from GitHub's fork-based model:

1. **No forks.** Contributors push directly to the source repo via special git refs.
2. **Custom refs, not branches.** PRs use `refs/pr/{NUMBER}` refs (not `refs/heads/`). These are not fetched by default when cloning.
3. **Discussions and PRs are the same type.** They share the same list view, same API, same data model. A PR is a discussion with `is_pull_request=True` and file changes attached.
4. **Draft by default.** Programmatically created PRs start in `"draft"` status. They must be manually published before merging.

The git ref model:

| PR # | Ref Path | Storage |
|------|----------|---------|
| 42 | `refs/pr/42` | All PR commits stored here |
| 42 (after merge) | `refs/pr/42` | Still exists until explicitly deleted |

### Full Python SDK Method Reference

From `huggingface_hub.HfApi` (v1.24.0):

#### 1. create_discussion() — Create Discussion or PR

```python
def create_discussion(
    repo_id: str,
    title: str,                                           # 3-200 chars
    *,
    token: bool | str | None = None,
    description: str | None = None,                       # Optional PR body
    repo_type: str | None = None,                         # None/model, dataset, space
    pull_request: bool = False,                           # False=discussion, True=PR
) -> DiscussionWithDetails
```

- PRs created programmatically are **always in draft status**
- To create a PR with actual file changes, use `create_commit()` with `create_pr=True` instead

#### 2. create_pull_request() — Wrapper for PR Creation

```python
def create_pull_request(
    repo_id: str,
    title: str,
    *,
    token: bool | str | None = None,
    description: str | None = None,
    repo_type: str | None = None,
) -> DiscussionWithDetails
```

Thin wrapper around `create_discussion(pull_request=True)`.

#### 3. get_discussion_details() — Fetch Single Discussion/PR

```python
def get_discussion_details(
    repo_id: str,
    discussion_num: int,
    *,
    repo_type: str | None = None,
    token: bool | str | None = None,
) -> DiscussionWithDetails
```

Returns full details including events, comments, and diff (for PRs).

#### 4. get_repo_discussions() — List Discussions/PRs

```python
def get_repo_discussions(
    repo_id: str,
    *,
    author: str | None = None,                            # Filter by author
    discussion_type: DiscussionTypeFilter | None = None,  # "all", "pull_request", "discussion"
    discussion_status: DiscussionStatusFilter | None = None, # "open", "closed", "all"
    repo_type: str | None = None,
    token: bool | str | None = None,
) -> Iterator[Discussion]
```

Returns an **iterator** of `Discussion` objects (not `DiscussionWithDetails`). To get full details, pass each `discussion.num` to `get_discussion_details()`.

#### 5. comment_discussion() — Post Comment

```python
def comment_discussion(
    repo_id: str,
    discussion_num: int,
    comment: str,
    *,
    token: bool | str | None = None,
    repo_type: str | None = None,
) -> DiscussionComment
```

Creates a new comment. Returns the created `DiscussionComment` object.

#### 6. edit_discussion_comment() — Edit Comment

```python
def edit_discussion_comment(
    repo_id: str,
    discussion_num: int,
    comment_id: str,
    new_content: str,
    *,
    token: bool | str | None = None,
    repo_type: str | None = None,
) -> DiscussionComment
```

Edits an existing comment. Requires either comment authorship or write access.

#### 7. hide_discussion_comment() — Hide Comment

```python
def hide_discussion_comment(
    repo_id: str,
    discussion_num: int,
    comment_id: str,
    *,
    token: bool | str | None = None,
    repo_type: str | None = None,
) -> DiscussionComment
```

Hides a comment (irreversible). Requires write access.

#### 8. change_discussion_status() — Open/Close

```python
def change_discussion_status(
    repo_id: str,
    discussion_num: int,
    new_status: Literal['open', 'closed'],
    *,
    token: bool | str | None = None,
    comment: str | None = None,     # Optional reason for status change
    repo_type: str | None = None,
) -> DiscussionStatusChange
```

Closes or re-opens a discussion/PR. Cannot close an already-merged PR.

#### 9. merge_pull_request() — Merge PR

```python
def merge_pull_request(
    repo_id: str,
    discussion_num: int,
    *,
    token: bool | str | None = None,
    comment: str | None = None,
    repo_type: str | None = None,
) -> DiscussionStatusChange
```

Merges a published (non-draft) Pull Request. After merging, the PR ref persists until explicitly deleted.

#### 10. rename_discussion() — Rename Title

```python
def rename_discussion(
    repo_id: str,
    discussion_num: int,
    new_title: str,
    *,
    token: bool | str | None = None,
    repo_type: str | None = None,
) -> DiscussionTitleChange
```

Renames a discussion/PR title. Requires authorship or write access.

### Data Classes

#### Discussion (summary-level, from get_repo_discussions)
| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | Discussion/PR title (3-200 chars) |
| `status` | `Literal['open', 'closed', 'merged', 'draft']` | Current state |
| `num` | `int` | Discussion number |
| `repo_id` | `str` | Namespace/repo |
| `repo_type` | `str` | model, dataset, or space |
| `author` | `str` | Creator's username |
| `is_pull_request` | `bool` | True if PR |
| `created_at` | `datetime` | Creation timestamp |
| `endpoint` | `str` | Hub endpoint URL |

#### DiscussionWithDetails (full, from get_discussion_details)
Extends `Discussion` with:

| Field | Type | Description |
|-------|------|-------------|
| `events` | `list[DiscussionEvent]` | All events (comments, status changes, etc.) |
| `conflicting_files` | `list[str] | bool | None` | Conflicting files if merge conflict exists |
| `target_branch` | `str | None` | Target branch for PR (default: main) |
| `merge_commit_oid` | `str | None` | OID after merge |
| `diff` | `str | None` | Full diff for PR |

#### DiscussionComment
| Field | Type |
|-------|------|
| `id` | `str` |
| `type` | `str` |
| `created_at` | `datetime` |
| `author` | `str` |
| `content` | `str` |
| `edited` | `bool` |
| `hidden` | `bool` |

#### DiscussionEvent (base class for all events)
Comments, status changes, title changes, and PR merges are all subtypes of events.

### Filtering & Enum Values

**DiscussionTypeFilter:**
- `"all"` (default) — both discussions and PRs
- `"pull_request"` — only PRs
- `"discussion"` — only discussions

**DiscussionStatusFilter:**
- `"open"` — open discussions/PRs (includes draft PRs)
- `"closed"` — closed or merged
- `"all"` (default) — both

### Status Lifecycle

```
create_discussion(pull_request=True)
  └─> status="draft" (programmatic PRs start here)
       └─> User clicks "Publish" on web UI
            └─> status="open"
                 ├─> merge_pull_request() → status="merged"
                 └─> change_discussion_status("closed") → status="closed"

create_discussion(pull_request=False)  (or via web UI)
  └─> status="open"
       └─> change_discussion_status("closed") → status="closed"
```

**Important constraints:**
- Draft → Open is **irreversible** (only via web UI "Publish" button)
- Closed → Open is reversible via `change_discussion_status("open")`
- Merged PRs cannot be reopened

### Git Workflow for PRs

#### Fetch a PR locally:
```bash
git fetch origin refs/pr/42:pr/42
git checkout pr/42
```

#### Make changes and push:
```bash
# Make changes
git add .
git commit -m "Your changes"
git push origin pr/42:refs/pr/42
```

#### Fetch ALL PRs (power-user):
```bash
git fetch origin refs/pr/*:refs/remotes/origin/pr/*
```

#### Delete PR ref after merge/close (frees storage):
After closing or merging a PR, the Hub shows a "Delete ref" button in the UI. This is irreversible but frees storage.

### Creating a PR with Changes (Single Call)

Rather than creating a draft PR and pushing changes separately, you can create a PR with changes atomically using `create_commit()`:

```python
from huggingface_hub import HfApi, CommitOperationAdd

api = HfApi()
api.create_commit(
    repo_id="user/repo",
    operations=[CommitOperationAdd(path_in_repo="file.txt", path_or_fileobj=b"content")],
    commit_message="Add file via PR",
    create_pr=True,              # Creates PR instead of committing directly
)
```

This is the preferred method for programmatic PR creation with changes.

### Practical CI/CD Patterns

| Pattern | Approach |
|---------|----------|
| **Simple PR from CI** | `create_commit(create_pr=True)` with file changes |
| **Multi-file PR** | Batch `CommitOperationAdd` operations in one `create_commit` call |
| **Review workflow** | Create draft PR, add reviewers via comments, merge when approved |
| **Contribution portal** | List all open PRs with `get_repo_discussions(type="pull_request", status="open")` |
| **Storage cleanup** | After merge, notify user to delete PR ref |
| **Closed PR audit** | `get_repo_discussions(status="closed")` filtered by type and date |

### Zero-Cost Considerations

- **Creating PRs is free** — all API calls are free-tier supported
- **PR refs take storage** — each PR stores its own git history. After merging, delete the ref to reclaim space (especially important for Hub's 5GB free storage limit)
- **No cost for comments/discussions** — all operations are REST API calls

### Resources
- Hub docs: https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions
- Python SDK: `huggingface_hub.HfApi` methods (v1.24.0)
  - Source-verified against `/opt/data/.venv-sakthai/lib/python3.14/site-packages/huggingface_hub/hf_api.py`
- CLI: `huggingface-cli discussions --help`
