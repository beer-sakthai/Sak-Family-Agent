# HF Hub Storage Management — Reference Notes

*Captured: 2026-07-23 from official HF docs*

## Storage Plans (from huggingface.co/docs/hub/en/storage-limits)

### Free Tier
- Limited storage quota for public repos
- Single file limit: 50GB via Git/LFS, 200GB via Xet
- Branch commit limit: recommend <500 commits

### PRO (paid)
- Higher storage limits
- Public Storage add-on available (purchase additional GB)
- Private storage PAYG (per-GB pricing for private repos)

### Team / Enterprise
- Highest limits, dedicated support
- Storage grants for research/non-profit (case-by-case)
- Contact: datasets@huggingface.co or models@huggingface.co

## Cleanup Operations (destructive, irreversible)

### LFS File Deletion (Web UI)
Settings → "List LFS files" → find file → delete action
⚠️ Deleting LFS *pointers* (`.gitattributes` entries) does NOT free space
⚠️ Future checkouts of branches referencing deleted LFS OIDs will fail
✅ Mitigation: `git config --global lfs.skipdownloaderrors true`

### PR Ref Deletion (Web UI)
Closed/merged PRs store commits in refs. Open the PR page → look for storage notice at bottom → "Delete ref"
Good for: PRs with large unmerged files, squashed branches with orphaned LFS versions

### Super-Squash (Python API only)
```python
HfApi().super_squash_history("username/repo")
```
- Compresses entire history to 1 commit
- LFS file history permanently removed
- Storage quota update takes up to 36 hours
- ⚠️ Irreversible — only use when you're sure

### Tracking LFS Origins
```bash
git log --all -p -S <sha256-oid>
```

## Python API Methods (huggingface_hub >= 0.20)

| Method | Purpose |
|--------|---------|
| `HfApi.list_lfs_files(repo_id)` | List all tracked LFS files |
| `HfApi.super_squash_history(repo_id)` | Compress history to 1 commit |
| `HfApi.delete_branch(repo_id, branch)` | Delete branch ref |
| `HfApi.list_repo_refs(repo_id)` | List all branches/tags/PR refs |

## Xet Storage (next-gen HF backend)
- Better dedup + compression than pure LFS
- Backward compatible with Git LFS
- Init: `git xet install` in cloned repo
- Track custom exts: `git xet track "*.ext"`
- Default for repos above certain thresholds
