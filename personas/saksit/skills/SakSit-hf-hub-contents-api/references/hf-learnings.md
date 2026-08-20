# HF Learnings — HF Hub Contents API

**Topic:** hf-hub-contents-api-deep-dive  
**Date:** 2026-07-24  
**Author:** SakThai  
**Source:** huggingface_hub v1.24.0 source code (`hf_api.py`)

---

## Summary

Comprehensive reference for the Hugging Face Hub's Repository Contents API — the methods and dataclasses in `huggingface_hub` for listing, inspecting, and navigating repo file trees, getting detailed path metadata (size, LFS info, security scan results, last commit), enumerating branches/tags/refs, and querying commit history. All methods live on `HfApi` and are also exposed as module-level functions.

---

## 1. `list_repo_tree()` — Navigate Repo File Trees

```python
def list_repo_tree(
    self,
    repo_id: str,
    path_in_repo: str | None = None,
    *,
    recursive: bool = False,
    expand: bool = False,
    revision: str | None = None,
    repo_type: str | None = None,
    token: str | bool | None = None,
) -> Iterable[RepoFile | RepoFolder]:
```

**Purpose:** List files and folders in a repo directory tree. Returns an iterable (generator) of `RepoFile` and `RepoFolder` objects.

### Parameters

| Parameter | Description |
|-----------|-------------|
| `repo_id` | Namespace/repo-name (e.g., `"bert-base-uncased"`) |
| `path_in_repo` | Relative subdirectory path. Defaults to root. |
| `recursive` | If True, lists all nested files/folders recursively |
| `expand` | If True, fetches additional metadata (last commit, security scan). Server limits to 50 results/page vs 1000. Pagination is transparent. |
| `revision` | Git revision (branch name, tag, commit hash). Defaults to `"main"`. |
| `repo_type` | `"model"`, `"dataset"`, `"space"`, or `"kernel"`. Defaults to `"model"`. |

### How It Works

Calls the Hub's tree API endpoint:
```
GET {endpoint}/api/{repo_type}s/{repo_id}/tree/{revision}/{path_in_repo}
?recursive={bool}&expand={bool}
```

Uses `paginate()` for transparent page traversal. Each response item with `type: "file"` becomes `RepoFile`, with `type: "folder"` becomes `RepoFolder`.

### Examples

```python
from huggingface_hub import list_repo_tree

# List root directory (non-recursive)
tree = list(list_repo_tree("bert-base-uncased"))
# → [RepoFile(path='.gitattributes', ...), RepoFile(path='README.md', ...), ...]

# List recursive with expanded metadata
tree = list(list_repo_tree("prompthero/openjourney-v4", expand=True))
# → Includes last_commit and security info on each entry

# List a subdirectory
tree = list(list_repo_tree("bigcode/the-stack", path_in_repo="data/python", repo_type="dataset"))
```

---

## 2. `get_paths_info()` — Get Metadata for Specific Paths

```python
def get_paths_info(
    self,
    repo_id: str,
    paths: list[str] | str,
    *,
    expand: bool = False,
    revision: str | None = None,
    repo_type: str | None = None,
    token: str | bool | None = None,
) -> list[RepoFile | RepoFolder]:
```

**Purpose:** Get metadata for one or more specific paths in a repo. Unlike `list_repo_tree`, you specify exact paths (not a directory). Missing paths are silently ignored — no exception raised.

### Parameters

| Parameter | Description |
|-----------|-------------|
| `repo_id` | Namespace/repo-name |
| `paths` | One or more exact file/folder paths relative to repo root |
| `expand` | If True, includes last commit and security scan data |
| `revision` | Git revision. Defaults to `"main"`. |
| `repo_type` | `"model"`, `"dataset"`, or `"space"`. Defaults to `"model"`. |

### Notes

- Non-existent paths are silently **ignored** — the result list may be shorter than the input paths list
- Useful for checking if specific files exist without raising errors
- Returns `RepoFile` for files, `RepoFolder` for directories

### Example

```python
from huggingface_hub import get_paths_info

paths_info = get_paths_info("allenai/c4", ["README.md", "en"], repo_type="dataset")
# → [
#     RepoFile(path='README.md', size=2379, blob_id='f84cb4c97182890fc1dbdeaf1a6a468fd27b4fff', lfs=None, ...),
#     RepoFolder(path='en', tree_id='dc943c4c40f53d02b31ced1defa7e5f438d5862e', ...)
#   ]
```

---

## 3. `list_repo_files()` — Flat File List

```python
def list_repo_files(
    self,
    repo_id: str,
    *,
    revision: str | None = None,
    repo_type: str | None = None,
    token: str | bool | None = None,
) -> list[str]:
```

**Purpose:** Get a flat list of all file paths in a repo. Only returns string paths — no metadata. Simpler and faster than `list_repo_tree` if you only need paths.

### Returns

`list[str]` — just the file paths, e.g.:
```python
['.gitattributes', 'README.md', 'config.json', 'pytorch_model.bin', 'vocab.json']
```

### Difference from `list_repo_tree`

| Aspect | `list_repo_files` | `list_repo_tree` |
|--------|-------------------|-------------------|
| Returns | Flat `list[str]` | Iterable of `RepoFile`/`RepoFolder` |
| Metadata | None | Size, blob_id, LFS, security, last_commit |
| Recursive | Always recursive | Controlled by `recursive` flag |
| Folders | Not included | Included as `RepoFolder` |

---

## 4. `list_repo_refs()` — Branches, Tags, and PR Refs

```python
def list_repo_refs(
    self,
    repo_id: str,
    *,
    repo_type: str | None = None,
    include_pull_requests: bool = False,
    token: str | bool | None = None,
) -> GitRefs:
```

**Purpose:** List all git references (branches, tags, and optionally pull requests) for a repo on the Hub.

### Returns

`GitRefs` dataclass with fields:
- `branches: list[GitRefInfo]` — branch refs
- `converts: list[GitRefInfo]` — internal "convert" refs used for dataset preprocessing
- `tags: list[GitRefInfo]` — tag refs
- `pull_requests: list[GitRefInfo] | None` — PR refs (only if `include_pull_requests=True`)

Each `GitRefInfo` has:
- `name: str` — e.g., `"main"`, `"v1.0"`
- `ref: str` — full git ref path, e.g., `"refs/heads/main"`, `"refs/tags/v1.0"`
- `target_commit: str` — commit OID, e.g., `"e7da7f221d5bf496a48136c0cd264e630fe9fcc8"`

### Examples

```python
from huggingface_hub import HfApi
api = HfApi()

# Basic usage
refs = api.list_repo_refs("gpt2")
# GitRefs(
#   branches=[GitRefInfo(name='main', ref='refs/heads/main', target_commit='e7da7f...')],
#   converts=[], tags=[]
# )

# With PRs
refs = api.list_repo_refs("bigcode/the-stack", repo_type="dataset", include_pull_requests=True)

# Usage pattern: find all branches
branches = [b.name for b in refs.branches]

# Usage pattern: check if a tag exists
has_v1 = any(t.name == "v1.0" for t in refs.tags)

# Usage pattern: get commit for a specific branch
main_commit = next(b.target_commit for b in refs.branches if b.name == "main")
```

---

## 5. `list_repo_commits()` — Commit History

```python
def list_repo_commits(
    self,
    repo_id: str,
    *,
    repo_type: str | None = None,
    token: str | bool | None = None,
    revision: str | None = None,
    formatted: bool = False,
) -> list[GitCommitInfo]:
```

**Purpose:** Get the list of commits for a given revision. Commits are sorted by date (newest first).

### Parameters

| Parameter | Description |
|-----------|-------------|
| `revision` | Git revision to query from. Defaults to head of `"main"` branch. |
| `formatted` | If True, returns HTML-formatted title and description. |

### Returns

`list[GitCommitInfo]` — each contains:
- `commit_id: str` — OID
- `authors: list[str]` — commit authors
- `created_at: datetime` — UTC timestamp
- `title: str` — commit title
- `message: str` — commit description
- `formatted_title: str | None` — HTML-formatted title (if `formatted=True`)
- `formatted_message: str | None` — HTML-formatted message (if `formatted=True`)

### Example

```python
from huggingface_hub import HfApi
api = HfApi()

# Get initial commit
commits = api.list_repo_commits("gpt2")
initial_commit = commits[-1]  # Last = oldest

# Initial commit is always a system commit with .gitattributes
# GitCommitInfo(
#   commit_id='9b865efde13a30c13e0a33e536cf3e4a5a9d71d8',
#   authors=['system'],
#   created_at=datetime(2019, 2, 18, 10, 36, 15, tzinfo=timezone.utc),
#   title='initial commit',
#   message=''
# )

# Create branch from initial commit (useful for empty branches)
api.create_branch("gpt2", "new_empty_branch", revision=initial_commit.commit_id)
```

---

## 6. Branch Management APIs

### `create_branch()`

```python
def create_branch(
    self,
    repo_id: str,
    *,
    branch: str,
    revision: str | None = None,
    token: str | bool | None = None,
    repo_type: str | None = None,
    exist_ok: bool = False,
) -> None:
```

Creates a new branch from an optional revision. If `revision` is None, creates from the current head of `"main"`. If `exist_ok=True`, silently succeeds if the branch already exists.

### `delete_branch()`

```python
def delete_branch(
    self,
    repo_id: str,
    *,
    branch: str,
    token: str | bool | None = None,
    repo_type: str | None = None,
) -> None:
```

Deletes a branch. Raises error if branch doesn't exist or you're trying to delete the default branch.

### `super_squash_history()`

```python
def super_squash_history(
    self,
    repo_id: str,
    *,
    branch: str | None = None,
    commit_message: str | None = None,
    repo_type: str | None = None,
    token: str | bool | None = None,
) -> None:
```

Squashes the entire git history of a branch into a single commit. Irreversible. Useful for cleaning up a repo with bloated history. Non-default branches only (cannot squash main).

---

## 7. Core Dataclasses Reference

### `RepoFile`

```python
@dataclass
class RepoFile:
    path: str              # Relative path from repo root
    size: int              # File size in bytes
    blob_id: str           # Git object OID
    lfs: BlobLfsInfo | None         # LFS metadata if file is LFS-tracked
    xet_hash: str | None            # Xet hash if file is Xet-stored
    last_commit: LastCommitInfo | None  # Only if expand=True
    security: BlobSecurityInfo | None   # Only if expand=True
```

### `RepoFolder`

```python
@dataclass
class RepoFolder:
    path: str              # Relative path from repo root
    tree_id: str           # Git tree OID
    last_commit: LastCommitInfo | None  # Only if expand=True
```

### `BlobLfsInfo`

```python
@dataclass
class BlobLfsInfo:
    size: int              # Actual file size
    sha256: str            # LFS content hash (SHA-256)
    pointer_size: int      # Size of the LFS pointer file in the repo
```

### `BlobSecurityInfo`

```python
@dataclass
class BlobSecurityInfo:
    safe: bool             # True if all scans passed
    status: str            # e.g., "safe", "unknown"
    av_scan: dict          # Antivirus scan result
    pickle_import_scan: dict | None  # Pickle import analysis
```

### `LastCommitInfo`

```python
@dataclass
class LastCommitInfo(dict):  # Also acts as dict for backward compat
    oid: str               # Commit OID
    title: str             # Commit title
    date: datetime         # UTC datetime
```

### `GitRefs`

```python
@dataclass
class GitRefs:
    branches: list[GitRefInfo]
    converts: list[GitRefInfo]
    tags: list[GitRefInfo]
    pull_requests: list[GitRefInfo] | None = None
```

### `GitRefInfo`

```python
@dataclass
class GitRefInfo:
    name: str              # e.g., "main", "v1.0"
    ref: str               # e.g., "refs/heads/main"
    target_commit: str     # Commit OID the ref points to
```

### `GitCommitInfo`

```python
@dataclass
class GitCommitInfo:
    commit_id: str
    authors: list[str]
    created_at: datetime
    title: str
    message: str
    formatted_title: str | None
    formatted_message: str | None
```

---

## 8. API Endpoints Under the Hood

All these methods call the Hub's REST API:

| Method | HTTP Request |
|--------|-------------|
| `list_repo_tree` | `GET /api/{repo_type}s/{repo_id}/tree/{revision}/{path}?recursive=&expand=` |
| `get_paths_info` | `GET /api/{repo_type}s/{repo_id}/paths-info/{revision}` with JSON body `{"paths": [...]}` |
| `list_repo_files` | `GET /api/{repo_type}s/{repo_id}/tree/{revision}?recursive=true` (same as tree with recursive) |
| `list_repo_refs` | `GET /api/{repo_type}s/{repo_id}/refs` |
| `list_repo_commits` | `GET /api/{repo_type}s/{repo_id}/commits/{revision}` |
| `create_branch` | `POST /api/{repo_type}s/{repo_id}/branch` with JSON `{"branch": ..., "oid": ...}` |
| `delete_branch` | `DELETE /api/{repo_type}s/{repo_id}/branch/{branch}` |
| `super_squash_history` | `POST /api/{repo_type}s/{repo_id}/super-squash` |

The `expand` parameter for `list_repo_tree` and `get_paths_info` causes the server to join additional data (last commit + security scan), which is why it's rate-limited to 50 items/page.

---

## 9. Practical Patterns

### Pattern A: Check if a file exists without error handling

```python
from huggingface_hub import get_paths_info

result = get_paths_info("username/my-model", ["config.json", "nonexistent.txt"])
# Missing paths are silently ignored
config_file = next((r for r in result if r.path == "config.json"), None)
if config_file:
    print(f"config.json: {config_file.size} bytes")
```

### Pattern B: List only certain file types in a dataset

```python
from huggingface_hub import list_repo_tree

files = list(list_repo_tree("bigcode/the-stack", repo_type="dataset", recursive=True))
parquet_files = [f for f in files if f.path.endswith(".parquet")]
print(f"Found {len(parquet_files)} parquet files")
```

### Pattern C: Find large LFS files

```python
from huggingface_hub import list_repo_tree, get_paths_info

files = list(list_repo_tree("username/my-model", expand=True))
large_lfs = [f for f in files if isinstance(f, RepoFile) and f.lfs and f.lfs.size > 1_000_000_000]
for f in large_lfs:
    print(f"{f.path}: {f.lfs.size / 1e9:.1f}GB")
```

### Pattern D: Check latest commit timestamp for a repo

```python
from huggingface_hub import HfApi
api = HfApi()
commits = api.list_repo_commits("bert-base-uncased")
latest = commits[0]
print(f"Last updated: {latest.created_at} by {', '.join(latest.authors)}")
```

### Pattern E: Delete all branches except main

```python
refs = api.list_repo_refs("username/my-experiment")
for branch in refs.branches:
    if branch.name != "main":
        api.delete_branch("username/my-experiment", branch=branch.name)
        print(f"Deleted branch: {branch.name}")
```

### Pattern F: Find when a specific file was last changed

```python
from huggingface_hub import get_paths_info

info = get_paths_info("username/my-model", ["config.json"], expand=True)
if info and isinstance(info[0], RepoFile) and info[0].last_commit:
    lc = info[0].last_commit
    print(f"config.json last changed: {lc.date} — \"{lc.title}\"")
```

---

## 10. Edge Cases & Gotchas

1. **Missing paths in `get_paths_info`**: Silently dropped from results. If you pass 10 paths and 5 don't exist, you get 5 results. No error, no indication which ones were missing.

2. **`expand=True` pagination limit**: Server returns max 50 results per page when `expand=True` vs 1000 when `expand=False`. Pagination is transparent (controlled by `paginate()` helper) but the 50-item page limit makes requests slower for large trees.

3. **`list_repo_files` only returns files**: No folders included, unlike `list_repo_tree` which returns both `RepoFile` and `RepoFolder`.

4. **`super_squash_history` cannot squash `main`**: Only works on non-default branches. Also irreversible — use with extreme caution.

5. **`list_repo_refs` with `include_pull_requests=True`**: PR refs have `ref` format `refs/pr/{number}`. This can be a large list for repos with many PRs.

6. **`RepoFolder` vs `RepoFile` distinction**: Check `isinstance(obj, RepoFile)` to differentiate. The `type` field in the API response determines which dataclass is created.

7. **`LastCommitInfo` double inheritance**: Inherits from both `dict` and `dataclass` (via `__post_init__` calling `self.update(asdict(self))`). This means `last_commit["oid"]` and `last_commit.oid` both work — but also means it behaves like a shallow copy in some contexts.

8. **`RepoFile` field name mapping**: The API returns `oid` for blob ID but `RepoFile` stores it as `blob_id`. Similarly, `lfs` from API uses `oid` for sha256 and `pointerSize` (camelCase) — these are remapped in the constructor.

---

## 11. Related Topics

| Topic | Relationship |
|-------|-------------|
| hf-hub-commit-api (topic #56) | Lower-level commit/upload operations |
| hf-hub-repo-lifecycle-management (topic #135) | Repo creation, deletion, settings |
| hf-hub-models-api (topic #127) | Model metadata via `model_info()` |
| hf-hub-upload-strategies (topic #133) | Uploading content to repos |
| hf-hub-buckets-api (topic #104) | Storage buckets for large repos |
| hf-hub-pull-requests-and-discussions-api (topic #122) | PRs and discussions on repos |
