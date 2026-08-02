# HF Hub Storage Management — Deep Dive (2026-07-24)

## Summary
Comprehensive deep-dive into Hugging Face Hub storage management — how to monitor, free, and manage storage across all repo types (models, datasets, spaces, buckets). Covers the full Python API from source (`huggingface_hub` v1.24+), web UI operations, quotas, LFS lifecycle, Space volumes, and best practices for zero-cost storage management.

## Key Sources
- `huggingface_hub` source code (`hf_api.py` main branch, v1.24.0-dev)
- https://huggingface.co/docs/hub/en/storage-limits

---

## 1. Checking Storage Usage

### Via `repo_info()` — per-repo snapshot

Every repo info object (`ModelInfo`, `DatasetInfo`, `SpaceInfo`) has a `used_storage` field (int, bytes):

```python
from huggingface_hub import HfApi
api = HfApi()
info = api.repo_info("username/my-repo")
print(f"Used storage: {info.used_storage:,} bytes ({info.used_storage / 1e9:.2f} GB)")
```

- `used_storage` is `Optional[int]` — may be `None` if not available
- Available for all repo types: model, dataset, space

### Via `list_user_repos()` — namespace-level audit

Lists **all** repos (models, datasets, spaces, buckets) for a user or org with storage info:

```python
from huggingface_hub import list_user_repos

# Current user
for repo in list_user_repos():
    print(f"{repo.id} ({repo.type}): {repo.storage:,} bytes ({repo.storage_percent:.1f}% of quota)")

# Organization
for repo in list_user_repos(namespace="my-org"):
    print(f"{repo.id}: {repo.storage:,} bytes")
```

**`RepoStorageInfo` fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Repo ID (`username/repo-name`) |
| `type` | `str` | `model`, `dataset`, `space`, or `bucket` |
| `updated_at` | `datetime` | Last update timestamp |
| `visibility` | `str` | `public` or `private` |
| `storage` | `int` | Storage used in bytes |
| `storage_percent` | `float` | % of namespace's total storage |

**Endpoint:** `GET /api/settings/repositories` (user) or `GET /api/organizations/{namespace}/settings/repositories` (org)

---

## 2. Listing & Deleting LFS Files (Python API)

### List all LFS files

```python
for lfs_file in api.list_lfs_files("username/my-repo"):
    print(f"{lfs_file.filename}: {lfs_file.size:,} bytes (SHA: {lfs_file.file_oid[:12]}...)")
```

**`LFSFileInfo` fields:**
| Field | Type | Description |
|-------|------|-------------|
| `file_oid` | `str` | SHA-256 object ID (identifier for deletion) |
| `filename` | `str` | Possible filename for the LFS object |
| `oid` | `str` | LFS object OID |
| `pushed_at` | `datetime` | When the LFS object was pushed |
| `ref` | `Optional[str]` | Ref the object was pushed on |
| `size` | `int` | Object size in bytes |

### Permanently delete LFS files

```python
# 1. List all LFS files
lfs_files = api.list_lfs_files("username/my-repo")

# 2. Filter specific files (e.g., files in a folder or larger than 1 GB)
files_to_delete = [
    f for f in lfs_files
    if f.filename.startswith("checkpoints/")
    or f.size > 1_000_000_000  # > 1 GB
]

# 3. Delete them (with history rewrite)
api.permanently_delete_lfs_files(
    "username/my-repo",
    files_to_delete,
    rewrite_history=True,  # removes git pointer files too
)
```

**Critical details:**
- ⚠️ **Irreversible** — cannot be undone
- Objects are identified by SHA-256 OID, not path — a single OID may be referenced by multiple paths across commits
- `rewrite_history=True` (default) removes git file pointers referencing deleted OIDs — strongly recommended
- Batch size: up to 1000 files per API call (internally batched)
- Deleting `.gitattributes` LFS pointer entries alone does **NOT** free storage
- Mitigation for checkout failures: `git config --global lfs.skipdownloaderrors true`

---

## 3. Managing Branches, Tags, and PR Refs

### List all refs

```python
refs = api.list_repo_refs("username/my-repo", include_pull_requests=True)
print(f"Branches: {[b.name for b in refs.branches]}")
print(f"Tags: {[t.name for t in refs.tags]}")
print(f"Converted PRs: {[c.name for c in refs.converts]}")

# include_pull_requests=True also returns PR refs
if hasattr(refs, 'pull_requests'):
    for pr in refs.pull_requests:
        print(f"PR ref: {pr.ref}")
```

**`GitRefs` structure:**
- `branches`: `list[GitRefInfo]` — each with `name`, `ref`, `target_commit`
- `converts`: `list[GitRefInfo]` — converted PR refs
- `tags`: `list[GitRefInfo]`

### Delete a branch

```python
api.delete_branch("username/my-repo", branch="old-experiment-branch")
```

- ❌ Cannot delete protected branches (e.g., `main`)
- ❌ Raises `HfHubHTTPError` if branch doesn't exist

### Web UI: Delete PR refs
Closed/merged PRs create git refs that still consume storage:
1. Open the closed/merged PR on the Hub
2. Look for the storage notice showing estimated reclaimable space
3. Click **"Delete ref"** to permanently remove it

---

## 4. Super-Squash Repository History

**Compresses entire Git history into a single commit — frees storage by eliminating orphaned LFS objects.**

```python
api.super_squash_history(repo_id="username/repo-name")
```

**Rules:**
- ⚠️ **Irreversible** — commit history and LFS file history permanently lost
- ⚠️ Storage quota reflects changes within **36 hours**
- Only available via Python API or REST API (no web UI button)
- Does NOT delete the actual LFS objects — it rewrites history so old LFS pointers are no longer referenced

**Use when:**
- A repo has thousands of commits with large LFS files in intermediate versions
- You need to reclaim storage quota after many iterations of model training
- Before publishing a final model checkpoint with clean history

---

## 5. Checking and Claiming Storage Quotas

### Free tier limits (per HF account)
- **Storage:** Limited quota (varies, typically a few GB for repos)
- **Single file size:** 50 GB via Git/LFS, 200 GB via Xet
- **Max files per repo:** ~100k recommended (hard limit exists but not published)
- **Max files per folder:** ~10k recommended

### Storage grants
- Research/non-profit grants available case-by-case
- Contact `datasets@huggingface.co` or `models@huggingface.co`
- Requires demonstrated community impact (downloads, citations)

### PRO / Team upgrades
- Higher base storage limits
- Public Storage add-on: purchase additional GB
- Private storage: PAYG per-GB pricing

---

## 6. Space Storage Management (Volumes API)

### New Volume API (replaces deprecated storage tiers)

The old `request_space_storage()` / `delete_space_storage()` are **deprecated** (removed in v2.0). Use the new Volume API:

```python
from huggingface_hub import HfApi, Volume

api = HfApi()

# Mount volumes in a Space
api.set_space_volumes(
    "username/my-space",
    volumes=[
        Volume(type="model", source="username/my-model", mount_path="/models", read_only=True),
        Volume(type="bucket", source="username/my-bucket", mount_path="/data"),
        Volume(type="dataset", source="username/my-dataset", mount_path="/datasets", read_only=True),
    ],
)

# Remove all volumes
api.delete_space_volumes("username/my-space")
```

**`Volume` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | `"bucket"`, `"model"`, `"dataset"`, or `"space"` |
| `source` | `str` | Repo or bucket ID |
| `mount_path` | `str` | Path inside the Space container |
| `revision` | `Optional[str]` | Specific revision to mount (bucket-compatible?) |
| `read_only` | `Optional[bool]` | Mount as read-only |
| `path` | `Optional[str]` | Subpath within source to mount |

### At repo creation

```python
api.create_repo(
    "username/my-space",
    repo_type="space",
    space_sdk="gradio",
    space_volumes=[
        Volume(type="bucket", source="username/my-bucket", mount_path="/data"),
    ],
)
```

The old `space_storage` parameter (`"small"`, `"medium"`, `"large"`) is deprecated.

---

## 7. Upload Management

### `upload_large_folder()` — DEPRECATED (but documented for reference)

```python
# DEPRECATED — use upload_folder() instead
api.upload_large_folder(
    repo_id="username/my-dataset",
    folder_path="/path/to/data",
    repo_type="dataset",
    allow_patterns=["*.parquet", "*.json"],
    ignore_patterns=["*.tmp", "__pycache__"],
    num_workers=4,
    print_report=True,
    print_report_every=60,
)
```

**Why deprecated:** `upload_folder()` is now multi-commit by default and resilient to interruptions, making `upload_large_folder()` redundant.

**Legacy behavior:** Used `.cache/.huggingface/` manifest for resumability, multiple workers for parallel uploads.

### `upload_folder()` — current recommended method

```python
from huggingface_hub import upload_folder

upload_folder(
    repo_id="username/my-repo",
    folder_path="/path/to/folder",
    repo_type="model",
    path_in_repo="subfolder",   # optional: nest inside repo
    ignore_patterns=[".*", "__pycache__"],
    multi_commits=True,          # resilient to interruptions (default)
    create_pr=False,
)
```

**Multi-commit mode** (default) splits large uploads into multiple smaller commits for resiliency.

---

## 8. Browsing Repo Contents

### `list_repo_tree()` — explore directory structure

```python
for item in api.list_repo_tree("username/my-repo", recursive=True):
    if isinstance(item, RepoFile):
        print(f"FILE: {item.path} ({item.size:,} bytes)")
        if item.lfs:
            print(f"  LFS: {item.lfs['size']:,} bytes, SHA: {item.lfs['sha256'][:16]}...")
    elif isinstance(item, RepoFolder):
        print(f"DIR:  {item.path}")
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `path_in_repo` | `str` | Subfolder to list (default: root) |
| `recursive` | `bool` | Whether to recurse into subfolders |
| `expand` | `bool` | Fetch extra info (last commit, security scan). More expensive — 50 results/page instead of 1000 |
| `revision` | `str` | Branch/tag/commit to browse (default: `main`) |

**`RepoFile` key fields:** `path`, `size`, `blob_id`, `lfs` (dict with `size`, `sha256`, `pointer_size`), `last_commit`, `security`
**`RepoFolder` key fields:** `path`

---

## 9. HF Hub Web UI Storage Operations

### Settings page operations
1. **Repo Settings → Storage section**
2. **"List LFS files"** — shows all tracked LFS objects with sizes
3. **Delete individual files** — per-file deletion with confirmation
4. **Storage usage bar** — visual indicator of quota remaining

### PR ref cleanup
- Each closed/merged PR leaves a git ref consuming storage
- UI shows estimated reclaimable space per PR
- "Delete ref" button permanently removes the ref

### Storage Buckets (new feature)
- S3-compatible object storage for large datasets
- Accessed via `hf://buckets/` URI scheme
- Deployed in the Spaces container via Volume API
- Not subject to usual storage quotas
- Priced separately (free tier includes limited bucket storage)

---

## 10. Zero-Cost Storage Management Strategy

### Free tier optimization checklist
1. **Audit first:** `list_user_repos()` to see which repos consume the most
2. **LFS cleanup:** Delete intermediate checkpoints and stale model files
3. **Branch pruning:** Delete experimental branches (`delete_branch()`)
4. **PR ref cleanup:** Delete refs of merged/closed PRs (web UI)
5. **Super-squash:** For repos with many commits of large LFS files
6. **Use Xet storage** for repos with frequent partial updates (content-addressed dedup reduces total storage)

### What NOT to do
- ❌ Don't delete `.gitattributes` entries to "remove LFS" — only removes tracking, not storage
- ❌ Don't delete LFS files without rewriting history — old commits will fail on checkout
- ❌ Don't mix Xet and `hf_transfer` simultaneously
- ❌ Don't expect quota to update instantly after super-squash (up to 36h)

---

## 11. API Reference Table

| Method | Purpose | Destructive? |
|--------|---------|-------------|
| `repo_info().used_storage` | Check storage used by a repo | ❌ No |
| `list_user_repos()` | List all repos with storage info | ❌ No |
| `list_repo_tree()` | Browse repo contents | ❌ No |
| `list_lfs_files()` | List all LFS files in a repo | ❌ No |
| `permanently_delete_lfs_files()` | Delete specific LFS objects | ✅ Yes, irreversible |
| `list_repo_refs()` | List branches/tags/PR refs | ❌ No |
| `delete_branch()` | Delete a branch | ✅ Yes, irreversible |
| `super_squash_history()` | Compress Git history to 1 commit | ✅ Yes, irreversible |
| `set_space_volumes()` | Mount volumes in a Space | ❌ No (reversible) |
| `delete_space_volumes()` | Remove all volumes from a Space | ✅ Yes |
| `delete_repo()` | Delete entire repository | ✅ Yes, irreversible |

## Resources
- Source: `huggingface_hub/src/huggingface_hub/hf_api.py` (lines 88, 1647, 1981, 3567, 3828, 4034, 4269, 4349, 4504, 6179, 7002, 8990)
- Docs: https://huggingface.co/docs/hub/en/storage-limits
- Hub Python Library docs: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api
