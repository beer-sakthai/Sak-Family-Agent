---
name: SakThai-hf-hub-fork-and-sync
description: "name: SakThai-hf-hub-fork-and-sync"
---

# HF Hub Fork & Sync — Server-Side Repo Duplication, File Copy & Bucket Sync

## Overview
Server-side repo duplication (`duplicate_repo`), file copying (`copy_files`), and bucket sync (`sync_bucket`) enable full-history, zero-download copies on the Hub, plus rsync-style local↔cloud data sync. These operations preserve git history, LFS objects, and (optionally) Space configuration — all without a local round-trip for full-repo copies.

> **Note:** HF "forks" are not linked like GitHub forks. `duplicate_repo()` creates an independent server-side git clone with no automatic upstream tracking. See `references/hf-learnings.md` for fork sync workflows.

**Key capabilities:**

| Operation | Function | CLI Command |
|-----------|----------|-------------|
| Full repo copy | `duplicate_repo()` | `hf repos duplicate` |
| Selective file copy | `copy_files()` | `hf repos cp` / `hf cp` |
| Local↔bucket sync | `sync_bucket()` | `hf sync` |
| Jobs volume prep | `sync_job_volume()` | — |

## Quick Reference

### Duplicate a repo
```python
from huggingface_hub import duplicate_repo

# Simple fork
duplicate_repo("google/gemma-2b")

# Dataset with custom name
duplicate_repo("org/data", to_id="me/experiment", repo_type="dataset")

# Re-fork (overwrite existing)
duplicate_repo("org/model", to_id="me/model", exist_ok=True)
```

```bash
hf repos duplicate google/gemma-2b
hf repos duplicate org/data me/experiment --type dataset
hf repos duplicate org/model me/model --exist-ok
```

### Copy files between repos
```python
from huggingface_hub import copy_files

copy_files("hf://org/model/config.json", "hf://me/model/config.json")
```

```bash
hf repos cp hf://org/model/config.json hf://me/model/config.json
```

### Sync local↔bucket
```python
from huggingface_hub import HfApi
HfApi().sync_bucket("./data", "hf://buckets/me/bucket/data")
```

```bash
hf sync ./data hf://buckets/me/bucket/data
```

## See Also
- `references/hf-learnings.md` — Full deep-dive (379 lines) covering:
  - `duplicate_repo()` Python & CLI reference
  - `copy_files()` with `hf://` URI patterns
  - `sync_bucket()` with all flags (rsync-inspired)
  - `sync_job_volume()` for Jobs data mounting
  - 5 practical fork sync workflows (re-create, git merge, selective file, CI/CD, bucket)
  - Storage regions impact on copy operations
  - Zero-cost patterns for all operations
  - GitHub fork vs HF duplicate comparison
  - Complete error handling reference
