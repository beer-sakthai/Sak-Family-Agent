---
name: hf-hub-storage-limits
author: SakThai
license: MIT
description: >-
  Master Hugging Face Hub storage limits, plans, quotas, and management.
  Covers Free/PRO/Team/Enterprise storage tiers, add-ons, pay-as-you-go,
  per-repo limitations, LFS file management, PR ref cleanup, and
  super-squash history operations.
---

# Hugging Face Hub Storage Limits & Plans

## Overview
Understanding HF Hub storage limits is critical for managing large models, datasets, and Spaces without hitting quota caps. The Hub uses a tiered storage system with different limits for public vs private repos.

## Storage Tiers

| Account Type | Public | Private |
|---|---|---|
| Free | Best-effort | 100 GB |
| PRO | Up to 10 TB + add-on | 1 TB + PAYG |
| Team | 12 TB + 1 TB/seat | 1 TB/seat + PAYG |
| Enterprise | 200 TB + 1 TB/seat | 1 TB/seat + PAYG |

## Key Commands

```bash
# Check quota via API
python -c "from huggingface_hub import HfApi; api=HfApi(); print(api.get_namespace_quota())"

# Super-squash repo history
python -c "from huggingface_hub import HfApi; api=HfApi(); api.super_squash_history('username/repo')"

# Track LFS file origin
git log --all -p -S <sha256-oid>
```

## Per-Repo Limits
- Files: < 100k recommended
- Per folder: < 10k (hard cap)
- File size: < 200 GB recommended, 500 GB hard cap
- Commit: < 100 files (~50-100 recommended)

## Storage Management
1. Delete LFS files via Settings > List LFS files
2. Delete PR refs from closed/merged PR pages
3. Super-squash via API (irreversible, quota updates in 36h)
4. Use `upload_folder()` for auto-splitting large commits
