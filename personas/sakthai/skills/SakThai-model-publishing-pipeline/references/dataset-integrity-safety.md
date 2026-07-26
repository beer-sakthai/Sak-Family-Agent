# Dataset Integrity Safety — Append, Don't Overwrite

## The Problem

Subagents and automated scripts frequently overwrite datasets instead of appending. This happened twice in one session (2026-07-25), reducing 1,328 training examples to 300. Recovery required finding the correct git commit hash.

## Prevention Protocol

### Before any dataset modification

1. Record the remote count
2. Save the backup commit hash  
3. For subagent tasks: include "APPEND — do NOT replace" in context

### After any dataset operation

1. Compare remote count vs expected (original + added)
2. If count is wrong, revert using backup commit hash

### Why this happens

- `hf_hub_download()` returns cached files, not fresh ones
- A corrupted cache persists across the same session
- Always use `revision=BACKUP_HASH` to bypass cache during recovery

### Recovery Template

```python
from huggingface_hub import hf_hub_download, HfApi
BACKUP_HASH = "bbdde20621cc"
good = hf_hub_download(REPO, "data/train.jsonl", revision=BACKUP_HASH)
# combine with new data and re-upload
```
