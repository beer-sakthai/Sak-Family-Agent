# Deepening: Storage Buckets — S3-Compatible Mutable Object Storage (July 2026)

See `~/profiles/sakthai/skills/references/hf-learnings.md` for full deep-dive.

## What Changed
Storage Buckets are a brand-new repo type on the HF Hub — S3-compatible, non-versioned, mutable object storage built on Xet. Designed for training checkpoints, logs, pipeline intermediates, and agent scratch storage.

## Key Facts
- **CLI**: `hf buckets create/list/cp/sync/rm` commands
- **Python**: `create_bucket()`, `batch_bucket_files()`, `download_bucket_files()`, `sync_bucket()`, `HfApi().copy_files()`
- **S3 API**: Gateway at `https://s3.hf.co/<namespace>`, S3 creds from User Access Token
- **Access**: hf-mount (NFS/FUSE), volume mounts (Jobs/Spaces), `hf://buckets/` paths (fsspec)
- **Integrations**: pandas, DuckDB, Dask, PyArrow, PySpark, Datasets, SkyPilot, DVC, rclone
- **No versioning**: Files overwrite in place — no Git history bloat
- **Server-side copy**: Between Xet-tracked repos/buckets (instant via chunk hashes)
- **Linked models**: Add `buckets: [my-org/my-bucket]` to model card YAML

## Zero-Cost Relevance
- Free storage allowance on buckets (check hf.co/storage)
- No super-squash needed (no history) — ideal for Beer's zero-cost constraint
- Server-side copy avoids download/re-upload bandwidth costs
