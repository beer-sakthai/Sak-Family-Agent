# HF Learnings — Hugging Face Hub

## 2026-07-24: hf-hub-buckets-api-deep-dive — Bucket Object Storage (Topic #105)

### Summary
Comprehensive deep-dive into the **Hugging Face Hub Buckets API** — a full S3-compatible object storage system built into `huggingface_hub` v1.24.0+. Buckets provide file storage outside the Git/LFS model, accessible via `hf://buckets/...` URIs with batch operations, bidirectional sync, file filtering, and plan/apply workflows.

This is a **major new feature** in huggingface-hub v1.x — not available in the 0.x series.

### Core Concept

Buckets are **object storage containers** on the Hugging Face Hub. Unlike repos (which use Git + LFS), buckets are:
- **Git-free** — no commit history, no branching, no pull requests
- **Flat-ish** — hierarchical paths but no Git tree overhead
- **Batch-optimized** — add/delete multiple files in a single API call
- **Sync-native** — designed for bidirectional sync with local directories
- **XET-powered** — uses the Xet protocol for fast, deduplicated storage

**URL scheme:** `hf://buckets/{namespace}/{bucket_name}(/path/to/file)`

### Bucket Data Model

| Concept | Description |
|---------|-------------|
| **Bucket** | Top-level storage container, owned by a user or org |
| **File** | A blob stored in a bucket at a path (no Git tracking) |
| **Folder** | Virtual directory — created implicitly by file paths |
| **Prefix** | Path prefix for scoping operations (like S3 prefix) |
| **Namespace** | User or organization name that owns the bucket |

### CLI Commands (`hf buckets`)

The `hf` CLI (not `huggingface-cli`) provides full bucket management:

| Command | Description | Example |
|---------|-------------|---------|
| `create` | Create a new bucket | `hf buckets create user/my-bucket` |
| `list` / `ls` | List buckets or files in a bucket | `hf buckets list user/my-bucket -R` |
| `info` | Get bucket metadata | `hf buckets info user/my-bucket` |
| `delete` | Delete entire bucket and contents | `hf buckets delete user/my-bucket -y` |
| `remove` / `rm` | Remove individual files | `hf buckets rm user/my-bucket/file.txt` |
| `move` | Rename/move a bucket | `hf buckets move user/old user/new` |
| `cp` | Copy files to/from buckets | `hf cp file.txt hf://buckets/user/my-bucket/` |
| `sync` | Bidirectional sync local↔bucket | `hf sync /local/data hf://buckets/user/my-bucket` |

**`hf buckets create` options:**
- `--private` — create a private bucket (default: public)
- `--region` — `us` or `eu` (requires Team plan+)
- `--exist-ok` — don't error if bucket already exists

**`hf buckets ls`** has two modes:
1. **List buckets** (no argument or namespace only): `hf buckets list`
2. **List files** (bucket_id given): `hf buckets list user/my-bucket -R --tree`

Flags: `-R` (recursive), `-h` (human-readable sizes), `--tree` (tree format)

**`hf buckets rm`** supports:
- `-R` / `--recursive` — delete files under a prefix
- `--include "*.safetensors"` / `--exclude "*.tmp"` — filter patterns
- `--dry-run` — preview without deleting
- `-y` — skip confirmation

**`hf cp`** (unified copy across repos and buckets):
```bash
# Upload to bucket
hf cp ./model.safetensors hf://buckets/user/my-bucket/models/

# Download from bucket
hf cp hf://buckets/user/my-bucket/config.json ./config.json

# Pipe to stdout
hf cp hf://buckets/user/my-bucket/log.txt -

# Remote-to-remote (same region)
hf cp hf://buckets/user/source/path hf://buckets/user/dest/path
```

**`hf buckets sync`** — bidirectional sync:
```bash
# Upload local → bucket
hf sync ./data hf://buckets/user/my-bucket

# Download bucket → local
hf sync hf://buckets/user/my-bucket ./data

# Dry-run first
hf sync ./data hf://buckets/user/my-bucket --dry-run

# Delete remote files not in source
hf sync ./data hf://buckets/user/my-bucket --delete

# Pattern filtering
hf sync ./data hf://buckets/user/my-bucket --include "*.safetensors" --exclude "*.tmp"

# Ignore existing files (only upload new ones)
hf sync ./data hf://buckets/user/my-bucket --ignore-existing

# Only update existing files (don't upload new)
hf sync ./data hf://buckets/user/my-bucket --existing

# Save plan, review, apply
hf sync ./data hf://buckets/user/my-bucket --plan sync-plan.jsonl
hf sync --apply sync-plan.jsonl
```

### Python API (`HfApi`)

All bucket operations available via `HfApi`:

```python
from huggingface_hub import HfApi

api = HfApi()

# Create bucket
url = api.create_bucket("my-bucket", private=True)
print(url.uri.to_uri())  # hf://buckets/user/my-bucket

# List buckets
for bucket in api.list_buckets(namespace="user"):
    print(bucket.id, bucket.size, bucket.total_files)

# Bucket info
info = api.bucket_info("user/my-bucket")
print(info.size, info.total_files, info.private)

# List files (lazy iterator)
for item in api.list_bucket_tree("user/my-bucket", prefix="data/", recursive=True):
    if item.type == "file":
        print(f"  {item.path} ({item.size} bytes)")
    elif item.type == "directory":
        print(f"  {item.path}/")

# Upload files (batch)
api.batch_bucket_files(
    "user/my-bucket",
    add=[
        ("/local/file1.txt", "remote/path/file1.txt"),
        ("/local/file2.txt", "remote/path/file2.txt"),
        (b"raw bytes content", "config.json"),  # bytes also accepted
    ],
)

# Delete files (batch)
api.batch_bucket_files(
    "user/my-bucket",
    delete=["old-file.txt", "temp/data.tmp"],
)

# Copy files (cross-bucket or repo-to-bucket)
api.batch_bucket_files(
    "user/my-bucket",
    copy=[("xet_hash_here", "destination/path", "source_repo_type", "source_repo_id")],
)

# Download files
api.download_bucket_files(
    "user/my-bucket",
    files=[
        ("remote/path/file1.txt", "/local/destination/file1.txt"),
        # Can also pass BucketFile object (more efficient — skips metadata fetch)
    ],
)

# Get file metadata
meta = api.get_bucket_file_metadata("user/my-bucket", "config.json")
print(meta.size, meta.xet_file_data.hash)

# Bidirectional sync
plan = api.sync_bucket(
    source="./data",
    dest="hf://buckets/user/my-bucket",
    delete=True,           # delete remote files not in source
    include=["*.py"],      # only sync .py files
    exclude=["__pycache__"],
    dry_run=True,          # preview without executing
)
print(plan.summary())
```

### Sync API Details

`sync_bucket()` returns a `SyncPlan` object:

```python
plan = api.sync_bucket("./data", "hf://buckets/user/my-bucket")
summary = plan.summary()
# {'uploads': 3, 'downloads': 0, 'deletes': 0, 'skips': 1, 'total_size': 4096}

# Plan/apply pattern for review workflows:
plan = api.sync_bucket("./data", "hf://buckets/user/my-bucket", plan="plan.jsonl")
# ... review plan.jsonl ...
api.sync_bucket(apply="plan.jsonl")
```

**Sync comparison logic** (determines if a file needs upload/download):
1. If file exists on only one side → upload/download (new file)
2. If both sides exist → compare size AND mtime (within 1s window)
   - Size differs → upload/download
   - Source newer → upload/download  
   - Identical → skip
3. Modes:
   - `--ignore-sizes` → only compare mtime
   - `--ignore-times` → only compare size
   - `--existing` → skip files that don't exist on receiver
   - `--ignore-existing` → skip files that DO exist on receiver
   - `--delete` → remove files at destination not present in source

### Filter System

```python
# CLI:
hf sync ./data hf://buckets/user/data --include "*.py" --exclude "__pycache__"

# Filter file (--filter-from):
#   +*.py
#   -__pycache__/*
#   +*.json
#   -*.tmp

# Python:
plan = api.sync_bucket(
    "./data", "hf://buckets/user/data",
    include=["*.py", "*.json"],
    exclude=["*.tmp"],
    filter_from="./.hfignore",
)
```

Filter rules process in order: filter file first, then CLI patterns, then defaults. First matching rule wins.

### Bucket File Metadata

```python
meta = api.get_bucket_file_metadata("user/my-bucket", "model.safetensors")
# BucketFileMetadata:
#   size: int (bytes)
#   xet_file_data: XetFileData (hash + refresh route)

# Bulk metadata:
for file_info in api.get_bucket_paths_info("user/my-bucket", ["a.txt", "b.txt"]):
    print(file_info.path, file_info.size, file_info.xet_hash)
```

### `hf cp` Unified Copy

The `hf cp` command is a single, unified command for copying files across:
- Local ↔ Repo (models/datasets/spaces)
- Local ↔ Bucket
- Repo ↔ Repo (same region)
- Repo ↔ Bucket (repo-to-bucket only; bucket-to-repo not supported)

Sub-aliases `hf repos cp` and `hf buckets cp` provide context-guarded variants.

```bash
# Pipe support
cat config.json | hf cp - hf://buckets/user/my-bucket/config.json
hf cp hf://buckets/user/my-bucket/log.txt -  # pipe to stdout
```

### Zero-Cost Strategy

**Buckets are free** on Hugging Face Hub with per-user storage limits:
- Public buckets: free, unlimited storage (part of Hub's free tier)
- Private buckets: free with storage limits (same as private repos)
- No GPU/compute cost — pure object storage

**Practical uses for zero-cost setup:**
1. Backup model weights to buckets instead of repo LFS (reduces clutter)
2. Share large datasets as flat buckets (no Git overhead for contributors)
3. Store cron outputs, logs, and artifacts from scheduled jobs
4. Sync data between Spaces and local development without Git commits
5. Use `hf://buckets/...` URIs as simple file servers for web content

### Error Handling

- `BucketNotFoundError` — bucket doesn't exist (catch when listing for new buckets)
- `ValueError` — invalid bucket ID format, missing prefix, conflicting sync options
- Batch operations are atomic within a single `batch_bucket_files` call

### CLI — Hidden Features

- **`hf buckets create`** accepts short names (`my-bucket`) — auto-prepends namespace
- **`hf buckets ls` without args** lists all your buckets globally
- **`--tree`** flag gives a nice hierarchical view of files
- **`hf buckets rm --recursive`** with `--include` enables selective mass deletion
- **`hf buckets sync --plan`** saves a JSONL file; `--apply` replays it — enables CI review gate pattern

### Resources
- Source: `huggingface_hub/_buckets.py` (1244 lines) — core bucket logic
- Source: `huggingface_hub/cli/buckets.py` (679 lines) — CLI interface
- Source: `huggingface_hub/cli/_cp.py` — unified `hf cp` command
- 🔗 Hugging Face Hub docs: https://huggingface.co/docs/hub/storage-buckets
- 🔗 CLI reference: https://huggingface.co/docs/hub/en/cli/buckets

---

## 2026-07-24: hf-hub-python-api-v2 — Complete HfApi v1.x Reference (Topic #6 — Deep Dive v2)

### Summary
Comprehensive deep-dive into the **`huggingface_hub` Python library (v1.24.0)** — 161 public `HfApi` methods covering the complete Hugging Face Hub API surface. This is a v2 deep dive of Topic #6 (originally covered early in the learning cycle) and focuses on the **v1.x architecture** which introduced major new features: Buckets object storage, Webhooks API, Hub Jobs, Scheduled UV Jobs, Branches/Tags API, Discussion API, Access Request management, LFS management, Safetensors metadata inspection, Daily Papers API, and expanded Space management (25 methods).

### v1.x vs 0.x — What Changed

| Area | 0.x | 1.x |
|------|-----|-----|
| **API methods** | ~60 | **161** |
| **Object storage** | Git + LFS only | **Buckets** (`hf://buckets/...`) — Git-free, S3-compatible |
| **Jobs** | None | `run_job`, `run_uv_job`, `create_scheduled_job`, `create_scheduled_uv_job` |
| **Webhooks** | None | Full CRUD (7 methods) |
| **Collections** | Manual REST only | 8 methods |
| **Discussions** | None | 8 methods |
| **Branches/Tags** | `main` only | `create_branch`, `delete_branch`, `create_tag`, `delete_tag`, `list_repo_refs` |
| **Access requests** | None | 7 methods for gated repo management |
| **Space management** | Minimal (`space_info`) | 25 methods |
| **LFS management** | None | `list_lfs_files`, `permanently_delete_lfs_files`, `verify_repo_checksums` |
| **Safetensors metadata** | None | `get_safetensors_metadata`, `parse_safetensors_file_metadata` |
| **Large uploads** | `upload_folder` only | + `upload_large_folder` (parallel, resumable, progress reports) |
| **Repo refactoring** | None | `move_repo`, `duplicate_repo`, `super_squash_history` |

### Full Reference
See the main learnings file at `skills/references/hf-learnings.md` (appended under the same date/topic) for the complete comprehensive reference covering all 161 HfApi methods with code examples across all API categories: Repository CRUD, File Operations, Buckets, Spaces, Jobs, Webhooks, Collections, Discussions, Access Requests, Branches/Tags, LFS/Safetensors, Discovery, User/Org, and Zero-Cost recipes.
