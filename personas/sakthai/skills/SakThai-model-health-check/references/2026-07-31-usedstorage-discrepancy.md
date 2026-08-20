# usedStorage: 2× file-sum discrepancy as git-history-bloat signal

**Observed:** 2026-07-30 on `Nanthasit/sakthai-plus-1.5b`

## Numbers

| Metric | Value |
|--------|-------|
| File-content sum (tree/main) | 3,098,933,908 bytes (2.89 GiB) |
| HF-reported `usedStorage` | 6,186,356,180 bytes (5.76 GiB) |
| Ratio | **1.996×** — essentially double |

## Root cause

`usedStorage` reflects the **total billed storage** on HF Hub, which for Git-LFS repos includes:

1. **LFS object storage** — the actual weight files
2. **Git metadata** — commit history, tree objects, LFS pointer files stored in `.git/`
3. **Stale LFS blobs** — when a model.safetensors is re-uploaded (same filename, new blob), the old blob remains in LFS storage until garbage-collected. Each re-upload adds the full weight file size to `usedStorage` even though only the latest version is visible in the file tree.
4. **Re-upload patterns** — if the model was pushed, deleted, and re-pushed (e.g., during a model card update that required a fresh push), both the old and new copies contribute to `usedStorage`.

## Diagnostic value

A `usedStorage : file-sum` ratio significantly above **1.1×** indicates git-history bloat. Ratios near **2.0×** strongly suggest one re-upload cycle (the old weight blob wasn't cleaned). Ratios above **3×** suggest multiple cycles or large intermediate artifacts.

## How to detect programmatically

```python
file_sum = sum(f.get('size', 0) or 0 for f in tree_data)
used_storage = model_api.get('usedStorage', 0)
ratio = used_storage / file_sum if file_sum > 0 else 0

if ratio > 1.5:
    health_adjustment = -5  # repo hygiene penalty
    notes.append(f"Storage ratio {ratio:.1f}× suggests git history bloat")
```

## When to report

- Always report both values in the health check YAML (`total_repo_storage_bytes` and `hf_reported_storage_bytes`).
- In the assessment, flag ratios > 1.3× as a repo-hygiene concern with a recommendation to investigate (git gc, fresh push, etc.).
- The `usedStorage` value from `/api/models/{id}` is the authoritative billing figure — use it for the health score's repo hygiene component, but note the file-sum for the user's reference.

## Mitigation

HF doesn't expose a public API for manual LFS garbage collection. Mitigations:
- **Fresh push to a new repo** — upload weights to a new repository name, delete the old one
- **Contact HF support** for LFS storage compaction on existing repos
- **Use `git lfs prune` + `git gc --aggressive`** locally before the initial push to minimize bloat from the start
