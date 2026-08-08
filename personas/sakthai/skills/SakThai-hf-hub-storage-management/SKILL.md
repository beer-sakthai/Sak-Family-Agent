---
name: SakThai-hf-hub-storage-management
description: "Manage Hugging Face Hub storage — understand quotas, free space, delete LFS files, super-squash repos, and manage Git LFS on the Hub"
---
# HF Hub Storage Management

Trigger when: user asks about HF storage quotas, freeing space, cleaning LFS files, deleting model versions, managing repo storage, super-squashing repos.

## Storage Plans Overview

| Plan      | Storage           | Features                  |
|-----------|-------------------|---------------------------|
| Free      | Limited quota     | Public repos only         |
| PRO       | Higher + add-ons  | Public + private storage  |
| Team/Ent  | Highest           | Private PAYG, grants      |

## How to Free Storage Space

### 1. Delete Individual LFS Files (Web UI)
1. Navigate to repository **Settings** page
2. Click **"List LFS files"** in the **Storage** section
3. Review files by size, find what you want to remove
4. Use the actions menu to delete specific files
5. ⚠️ This is destructive and cannot be undone

### 2. Delete PR Refs
Closed or merged Pull Requests create git refs that still consume storage:
1. Open the closed/merged PR on the Hub
2. Look for the storage notice at the bottom showing estimated reclaimable space
3. Click **"Delete ref"** to permanently remove the PR ref
4. ⚠️ Irreversible — prevents anyone from fetching those commits

### 3. Super-Squash Repository (Python API)
Compresses entire Git history into a single commit:
```python
from huggingface_hub import HfApi
api = HfApi()
api.super_squash_history(repo_id="username/repo-name")
```
- ⚠️ **Irreversible** — commit history and LFS file history permanently lost
- Storage quota reflects changes within 36 hours
- Only available via Python API or REST API

### 4. Track LFS File References
Find which commit introduced a specific LFS file by its SHA-256 OID:
```bash
git log --all -p -S <SHA-256-OID>
```
Example output shows the commit, date, and diff that added/removed the file.

### 5. List All LFS Files (Python API)
```python
from huggingface_hub import HfApi
api = HfApi()
for lfs_file in api.list_lfs_files(repo_id="username/repo-name"):
    print(f"{lfs_file.path}: {lfs_file.size} bytes")
```

## Python API Reference

| Method                          | Description                              |
|---------------------------------|------------------------------------------|
| `HfApi.list_lfs_files(repo_id)` | List all LFS files and their sizes       |
| `HfApi.super_squash_history(repo_id)` | Compress to single commit          |
| `HfApi.delete_branch(repo_id, branch)` | Delete a branch ref               |
| `HfApi.list_repo_refs(repo_id)` | List all branches, tags, and PR refs     |

## Critical Warnings
- ❌ Deleting LFS **pointers** (`.gitattributes` entries) does NOT free storage
- ❌ Without rewriting history, future checkouts of branches referencing deleted LFS files will fail
- ✅ Prevent checkout failures: add `git config --global lfs.skipdownloaderrors true`
- ✅ Always backup important files before any destructive operation
- ⏱ Storage quota updates after super-squash take up to 36 hours

## Xet Storage (HF's Next-Gen Storage)
- Alternative to pure Git LFS with better deduplication and compression
- Initialize: `git xet install` in cloned repo
- Track custom extensions: `git xet track "*.ext"`
- Backward compatible with Git LFS

## HfFileSystem — Filesystem API

`HfFileSystem` provides an `fsspec`-compatible POSIX-like file interface to the Hugging Face Hub. It wraps `HfApi` and supports `ls`, `glob`, `cp`, `mv`, `du`, `open`, `read_text`, `put_file`, and `get_file`.

> ⚠ **Performance note**: HfFileSystem adds fsspec compatibility overhead. For direct operations prefer `HfApi` methods. Use HfFileSystem when you need fsspec integration (pandas, DuckDB, Zarr).

### Quick Start

```python
from huggingface_hub import hffs

# List files in a dataset directory
hffs.ls("datasets/my-username/my-dataset-repo/data", detail=False)

# Glob for CSV files
hffs.glob("datasets/my-username/my-dataset-repo/**/*.csv")

# Read a remote file
with hffs.open("datasets/my-username/my-dataset-repo/data/train.csv", "r") as f:
    train_data = f.readlines()

# Read as string (with optional revision/branch)
train_data = hffs.read_text("datasets/my-username/my-dataset-repo/data/train.csv", revision="dev")

# Write to a remote file
with hffs.open("datasets/my-username/my-dataset-repo/data/validation.csv", "w") as f:
    f.write("text,label\n")
    f.write("Fantastic movie!,good\n")
```

### hf:// URL Scheme

The `hf://` URI scheme enables third-party fsspec integration:

```
hf://[<repo_type_prefix>]<repo_id>[@<revision>]/<path/in/repo>
```

| Prefix     | Repo Type        |
|------------|------------------|
| *(none)*   | Model repos      |
| `datasets/`| Dataset repos    |
| `spaces/`  | Space repos      |
| `buckets/` | HF Buckets (S3)  |

### Key Integrations

**Pandas / Polars / Dask** — read/write DataFrames directly:
```python
import pandas as pd
df = pd.read_csv("hf://datasets/my-username/my-dataset-repo/train.csv")
df.to_csv("hf://datasets/my-username/my-dataset-repo/test.csv")
```

**DuckDB** — query remote files:
```python
from huggingface_hub import HfFileSystem
import duckdb

fs = HfFileSystem()
duckdb.register_filesystem(fs)
df = duckdb.query("SELECT * FROM 'hf://datasets/.../data.parquet' LIMIT 10").df()
```

**Zarr** — use the Hub as an array store:
```python
import zarr
import numpy as np

embeddings = np.random.randn(50000, 1000).astype("float32")
with zarr.open_group("hf://my-username/my-model-repo/array-store", mode="w") as root:
    foo = root.create_group("embeddings")
    foobar = foo.zeros('experiment_0', shape=(50000, 1000), chunks=(10000, 1000), dtype='f4')
    foobar[:] = embeddings
```

### Authentication

```python
from huggingface_hub import HfFileSystem
hffs = HfFileSystem(token="hf_...")  # or use `huggingface-cli login`
```

⚠ Never hardcode tokens in shared code — use environment variables or `huggingface-cli login`.

### Revision Support

Most operations accept a `revision=` parameter (branch, tag, commit hash). Note: revision is **not compatible** with Hugging Face Buckets.

### Known Limitations
- Binary mode by default (same as fsspec): explicitly pass `mode="r"` or `mode="w"` for text
- Appending (modes `"a"` / `"ab"`) not yet supported
- Buckets revision parameter not supported

## Related Skills
- [`mlops/huggingface-hub`](../huggingface-hub/SKILL.md) — HF CLI for repos, datasets, cache/prune, webhooks, general Hub ops
- [`mlops/spaces-zerogpu`](../spaces-zerogpu/SKILL.md) — ZeroGPU allocation planning (storage-related for Spaces)

## Research/Academic Grants
- Contact `datasets@huggingface.co` or `models@huggingface.co`
- Requires demonstrated community impact (downloads, citations)
- Case-by-case evaluation for high-impact open-source work
