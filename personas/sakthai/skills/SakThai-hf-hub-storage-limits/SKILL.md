---
name: SakThai-hf-hub-storage-limits
description: ">-   Master Hugging Face Hub storage ecosystem \u2014 Git-based repo limits,   Storage\
  \ Buckets (S3-compatible mutable object storage), quota   management, Xet dedup\
  \ backend, and zero-cost patterns."
---

# Hugging Face Hub Storage Limits, Plans & Storage Buckets

## Overview
HF Hub offers two storage paradigms: **Git-based repos** (models, datasets, Spaces) for versioned artifacts, and **Storage Buckets** (S3-like, non-versioned, mutable) for working storage. All data is backed by the Xet chunk-level dedup storage backend.

## Storage Plans

| Account Type | Public Storage | Private Storage |
|---|---|---|
| Free user/org | Best-effort | 100 GB |
| PRO | Up to 10 TB + add-on | 1 TB + PAYG |
| Team Org | 12 TB + 1 TB/seat + add-on | 1 TB/seat + PAYG |
| Enterprise | 200 TB + 1 TB/seat + add-on | 1 TB/seat + PAYG |

## Storage Buckets (New! — July 2026)
S3-compatible mutable object storage built on Xet. Unlike Git repos, buckets are **non-versioned** and **mutable** — files overwrite in place. Designed for checkpoints, logs, agent scratch storage, and pipeline intermediates.

### Buckets vs Repos
| Feature | Git Repos | Storage Buckets |
|---|---|---|
| Versioning | Full Git history | None (mutable, overwrite) |
| Types | Models, datasets, Spaces | Standalone bucket |
| Use case | Publishing finished artifacts | Working storage / intermediates |
| Operations | Hub API, Git push/pull | S3-like sync, cp, rm |
| Dedup | Xet chunk-level | Xet chunk-level |
| PRs | Yes | No |
| Cards | Yes | Plain README only |

### CLI Commands (`hf buckets`)
```bash
# Create
hf buckets create my-bucket
hf buckets create my-org/shared-bucket --private

# List contents
hf buckets list username/my-bucket -h -R
hf buckets list username/my-bucket --tree -h -R

# Upload / download / sync
hf buckets cp ./model.safetensors hf://buckets/username/my-bucket/model.safetensors
hf buckets cp hf://buckets/username/my-bucket/config.json - | jq .
hf buckets sync ./data hf://buckets/username/my-bucket/data --delete
hf sync ./checkpoints hf://buckets/my-org/training-run-42/checkpoints

# Delete (immediate, no undo!)
hf buckets rm username/my-bucket/old-model.bin
hf buckets rm username/my-bucket/logs/ --recursive --dry-run

# Server-side copy between repos/buckets (instant via Xet hashes)
hf buckets cp hf://datasets/HuggingFaceFW/fineweb/data hf://buckets/username/fineweb-data
```

### Python API
```python
from huggingface_hub import create_bucket, batch_bucket_files, download_bucket_files, sync_bucket

create_bucket("my-bucket", private=True)
batch_bucket_files("username/my-bucket", add=[("./model.safetensors", "models/model.safetensors")])
download_bucket_files("username/my-bucket", files=[("models/model.safetensors", "./local/model.safetensors")])
sync_bucket("./data", "hf://buckets/username/my-bucket/data")
HfApi().copy_files("hf://datasets/org/data", "hf://buckets/username/fineweb-data")
```

### S3-Compatible API
Gateway at `https://s3.hf.co/<namespace>`. Generate S3 creds from User Access Token dropdown.
```ini
[profile hf]
region = us-east-1
endpoint_url = https://s3.hf.co/<namespace>
s3 = addressing_style = path
request_checksum_calculation = when_required
response_checksum_validation = when_required
```
Works with AWS CLI, boto3, s5cmd, rclone, DVC, DuckDB (via httpfs).

### Access Patterns
- **hf-mount**: NFS/FUSE mount for any tool (`brew install hf-mount; hf-mount start bucket username/my-bucket /mnt/data`)
- **Volume mounts**: Jobs & Spaces mount buckets read-write automatically
- **hf:// paths** (fsspec): pandas, DuckDB, PyArrow, Dask, PySpark, Datasets lib all read `hf://buckets/...` natively
- **SkyPilot**: `store: hf` mounts buckets read-write across 20+ clouds

### Key Differences from S3
- No ACLs, policies, tags, versioning, lifecycle rules, SSE
- Only ListObjectsV2 (not V1)
- No cross-namespace server-side copy
- Multipart uploads expire after 7 days
- Single-region gateway (CDN caches at edges)

### Linked Models
Add `buckets: [my-org/my-bucket]` to model card YAML to link a bucket.

### Zero-Cost Patterns
1. Use Storage Buckets for training checkpoints instead of Git repos (no history bloat = no super-squash needed)
2. Free storage allowance on buckets — check hf.co/storage for latest
3. Server-side copy between repos/buckets avoids download/re-upload costs
4. Sync with `--dry-run` first to preview changes before committing resources

## Git Repo Limits
| Characteristic | Recommended | Hard Limit |
|---|---|---|
| Files per repo | < 100k | Soft (performance degrades) |
| Entries per folder | < 10k | Hard cap: 10k/folder |
| File size | < 200 GB | Hard cap: 500 GB |
| Commit size | < 100 files | Soft (60s HTTP timeout) |
| Commits per repo | — | Soft (UI degrades past few thousand) |

## Key Commands
```bash
# Check quota
python -c "from huggingface_hub import HfApi; api=HfApi(); print(api.get_namespace_quota())"

# Super-squash (destructive, quota updates in 36h)
python -c "from huggingface_hub import HfApi; api=HfApi(); api.super_squash_history('username/repo')"

# Track LFS file origin
git log --all -p -S <sha256-oid>
```

## Storage Management
1. **Delete LFS files**: Settings > List LFS files (deleting pointers alone doesn't free space)
2. **Delete PR refs**: Closed/merged PRs show reclaimable space at bottom
3. **Super-squash**: Irreversible, LFS history removed, quota updates in 36h
4. **Use `upload_folder()`** for auto-splitting large commits (~50-100 files)
5. **For large datasets**: Use Parquet or WebDataset formats, avoid custom loading scripts
