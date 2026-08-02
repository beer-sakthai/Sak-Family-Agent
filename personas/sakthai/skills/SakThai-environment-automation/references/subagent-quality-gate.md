# Subagent Quality Gate — Dataset & Upload Verification

Subagents can corrupt datasets, models, and repos by **overwriting instead of appending**. This reference defines the quality gate to prevent data loss.

## The Failure Pattern

```
Good dataset (1,328 examples) → Subagent reads, processes → Uploads
                                          ↓
                                    Only 300 examples remain
                                    (Original 1,028 LOST)
```

The subagent read the dataset, generated 100 new examples, and uploaded only the 100+200=300 it had in memory — discarding the 1,028 original examples. The cache returned stale data, and the subagent didn't check the remote count before acting.

## Quality Gate Protocol

### Before any dataset operation

1. **Record original count** — query the remote dataset and note line count
   ```python
   import requests
   remote = requests.get(f"https://huggingface.co/datasets/{repo}/raw/main/data/train.jsonl")
   print(f"Remote count: {len(remote.text.strip().split(chr(10)))}")
   ```

2. **Download fresh, not from cache** — force a new download by specifying a commit hash or clearing the cache
   ```python
   from huggingface_hub import hf_hub_download
   path = hf_hub_download(repo, "data/train.jsonl", revision=known_good_commit)
   ```

3. **Keep backup commit hash** — always store the SHA of the last good state before modifying

### After any dataset operation

4. **Verify remote count** — immediately after upload, re-query the remote dataset and assert the count equals original + added
   ```python
   new_remote = requests.get(f"https://huggingface.co/datasets/{repo}/raw/main/data/train.jsonl")
   actual = len(new_remote.text.strip().split(chr(10)))
   expected = original_count + added_count
   assert actual == expected, f"Expected {expected}, got {actual}"
   ```

5. **Never trust subagent output verbatim.** A subagent that says "uploaded successfully" may have overwritten the data. Always verify remotely.

### Recovery from corruption

```python
from huggingface_hub import HfApi, hf_hub_download

# Find the last good commit
api = HfApi()
commits = api.list_repo_commits(repo, repo_type="dataset")
for c in commits:
    # Download from this commit
    path = hf_hub_download(repo, "data/train.jsonl", revision=c.commit_id, repo_type="dataset")
    with open(path) as f:
        lines = f.readlines()
    if len(lines) >= original_count:
        print(f"Found good commit: {c.commit_id} ({len(lines)} lines)")
        # Re-upload
        api.upload_file(path_or_fileobj=path, path_in_repo="data/train.jsonl", ...)
        break
```

## Root Causes

| Cause | Symptom | Fix |
|-------|---------|-----|
| Cache staleness | hf_hub_download returns old version | Force revision= param |
| Subagent memory limit | Subagent only keeps N samples in context | Pre-validate count |
| Overwrite mode | upload_file replaces entire file | Use append where available |
| No count check | Upload succeeds but data lost | Always verify after |
