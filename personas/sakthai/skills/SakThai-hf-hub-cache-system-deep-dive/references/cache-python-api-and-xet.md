# Hugging Face Cache Python API, Xet Chunks & Symlink Handling

### `scan_cache_dir()` — Inspect

```python
from huggingface_hub import scan_cache_dir

hf_cache_info = scan_cache_dir()
# Optional: scan_cache_dir(cache_dir="/custom/path")

print(f"Total cache size: {hf_cache_info.size_on_disk} bytes")
print(f"Number of repos: {len(hf_cache_info.repos)}")
print(f"Incomplete files: {len(hf_cache_info.incomplete_files)}")
print(f"Warnings: {len(hf_cache_info.warnings)}")

# Iterate repos
for repo in sorted(hf_cache_info.repos, key=lambda r: r.size_on_disk, reverse=True):
    print(f"  {repo.repo_type}/{repo.repo_id}: {repo.size_on_disk} bytes ({repo.nb_files} files)")
    for revision in repo.revisions:
        refs = ", ".join(revision.refs) if revision.refs else "(detached)"
        print(f"    {revision.commit_hash[:7]} [{refs}] {revision.size_on_disk} bytes")
```

**Dataclasses returned:**

| Class | Key fields |
|-------|-----------|
| `HFCacheInfo` | `size_on_disk`, `repos` (frozenset), `incomplete_files`, `warnings` |
| `CachedRepoInfo` | `repo_id`, `repo_type`, `repo_path`, `size_on_disk`, `nb_files`, `revisions`, `last_accessed`, `last_modified` |
| `CachedRevisionInfo` | `commit_hash`, `snapshot_path`, `size_on_disk`, `files`, `refs`, `last_modified` |
| `CachedFileInfo` | `file_name`, `file_path`, `blob_path`, `size_on_disk`, `blob_last_accessed`, `blob_last_modified` |

### `delete_revisions()` — Delete

```python
from huggingface_hub import scan_cache_dir

# Build a deletion strategy
delete_strategy = scan_cache_dir().delete_revisions(
    "81fd1d6e7847c99f5862c9fb81387956d99ec7aa",
    "e2983b237dccf3ab4937c97fa717319a9ca1a96d",
)

print(f"Will free {delete_strategy.expected_freed_size_str}")

# Preview only — no files deleted yet
print(f"Blobs to delete: {len(delete_strategy.blobs)}")
print(f"Snapshots to delete: {len(delete_strategy.snapshots)}")
print(f"Repos to delete: {len(delete_strategy.repos)}")
print(f"Refs to delete: {len(delete_strategy.refs)}")

# Execute the deletion
delete_strategy.execute()
```

**Deletion rules:**
1. The snapshot folder (symlinks) is deleted
2. Blobs only referenced by deleted revisions are deleted
3. If a revision had refs, those refs are deleted
4. If all revisions of a repo are deleted, the entire repo folder is removed

### `try_to_load_from_cache()` — Check Without Network

```python
from huggingface_hub import try_to_load_from_cache, _CACHED_NO_EXIST

filepath = try_to_load_from_cache(
    repo_id="bert-base-uncased",
    filename="config.json",
    revision="main",
    repo_type="model",
)

if isinstance(filepath, str):
    # File exists and is cached
    print(f"Found at {filepath}")
elif filepath is _CACHED_NO_EXIST:
    # Non-existence is cached
    print("File known not to exist")
else:
    # Not in cache — would need network
    print("Not cached")
```

### `cached_assets_path()` — Downstream Library Assets

```python
from huggingface_hub import cached_assets_path

assets_path = cached_assets_path(
    library_name="datasets",
    namespace="SQuAD",
    subfolder="download",
)
# Result: ~/.cache/huggingface/assets/datasets/SQuAD/download/

# Write/read your own asset files
(assets_path / "processed.arrow").write_bytes(data)
```

Recommended for libraries that need their own cache alongside the Hub cache.

## Xet Chunk-Based Cache

Xet (`hf_xet`) adds a second caching layer for chunk-level deduplication (~64 KB chunks), used for Xet-enabled repositories.

### Directory structure

```
~/.cache/huggingface/xet/
└── <environment_identifier>/    # e.g. https___cas_serv-tGqkUaZf_CBPHQ6h
    ├── chunk_cache/             # Download optimization
    │   └── <base64-prefix>/     # First 2 chars of CAS hash
    │       └── <full-key>/      # Cached byte-range chunks
    ├── shard_cache/             # Upload optimization
    │   └── *.mdb               # Shard files (file→chunk mappings)
    └── staging/                 # Resumable upload workspace
        ├── shard-session/      # In-progress upload metadata
        └── xorb-metadata/      # Successfully uploaded chunks
```

### chunk_cache (download path)

- Content-addressed chunks (~64 KB each)
- Consulted before fetching from CAS — cache hit = no network call
- Eviction: random eviction when full (computationally cheapest)
- **Disabled by default** as of `hf_xet` 1.2.0 — enable via `HF_XET_CHUNK_CACHE_SIZE_BYTES`
- Default limit: 10 GB

### shard_cache (upload path)

- Maps files → chunk hashes for deduplication during upload
- If a shard shows a chunk already exists in CAS, it's skipped
- Shards expire after 3–4 weeks
- Soft limit: 4 GB

### staging (resumable uploads)

- Persists upload progress so interrupted uploads can resume without re-uploading chunks already sent
- On successful completion, staging content moves to shard_cache

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `HF_XET_CHUNK_CACHE_SIZE_BYTES` | 0 (disabled) | Max bytes for chunk cache (e.g. `10737418240` for 10 GB) |
| `HF_XET_SHARD_CACHE_SIZE_LIMIT` | 4 GB | Soft limit for shard cache |

**To clear Xet cache entirely:**
```bash
rm -rf ~/.cache/huggingface/xet
```

## Asset Caching

Downstream libraries (Datasets, Transformers, etc.) can store their own non-Hub files using `cached_assets_path()`. These live under `~/.cache/huggingface/assets/` and follow a `<library>/<namespace>/<subfolder>/` hierarchy.

```
~/.cache/huggingface/assets/
├── datasets/
│   ├── SQuAD/
│   │   ├── downloaded/
│   │   ├── extracted/
│   │   └── processed/
│   └── Helsinki-NLP--tatoeba_mt/
│       └── downloaded/
└── transformers/
    ├── default/
    │   └── something/
    └── bert-base-cased/
        └── default/
```

## Symlink Handling

### Linux / macOS

Symlinks are used by default. Blobs live in `blobs/`, and `snapshots/<revision>/` contains symlinks to them. This enables file sharing across revisions.

### Windows

Symlinks require either:
- **Developer Mode** (Windows 10/11)
- **Running Python as Administrator**

**Without symlinks** (fallback mode):
- Files are copied directly into `snapshots/<revision>/` instead of symlinking
- Cache works correctly but files are duplicated if the same blob appears in multiple revisions
- All management tools (scan, delete, prune) still work

### Controlling symlinks

```bash
# Force no-symlink mode (e.g. on shared filesystems)
export HF_HUB_DISABLE_SYMLINKS=1

# Suppress the "symlinks not supported" warning
export HF_HUB_DISABLE_SYMLINKS_WARNING=1
```

## Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_HOME` | `~/.cache/huggingface` | Root HF cache directory |
| `HF_HUB_CACHE` | `$HF_HOME/hub` | File-based cache location |
| `HF_ASSETS_CACHE` | `$HF_HOME/assets` | Assets cache location |
| `HF_HUB_DISABLE_SYMLINKS` | (unset) | `1` = disable symlinks, copy files directly |
| `HF_HUB_DISABLE_SYMLINKS_WARNING` | (unset) | `1` = suppress symlink warning |
| `HF_XET_CHUNK_CACHE_SIZE_BYTES` | 0 (disabled) | Enable Xet chunk cache with byte limit |
| `HF_XET_SHARD_CACHE_SIZE_LIMIT` | 4 GB | Xet shard cache soft limit |

## Pitfalls

| Pitfall | Symptom | Mitigation |
|---------|---------|------------|
| **Cache never deletes itself** | Disk fills up over time | Schedule `hf cache prune` periodically |
| **Symlinks not supported** | Warning on every download | Set `HF_HUB_DISABLE_SYMLINKS_WARNING=1` |
| **Windows without Developer Mode** | Files duplicated per revision | Accept the ~2x storage overhead, or enable Developer Mode |
| **Xet chunk cache fills disk** | `~/.cache/huggingface/xet` grows large | `rm -rf ~/.cache/huggingface/xet` or set `HF_XET_CHUNK_CACHE_SIZE_BYTES` |
| **`IncompleteSnapshotError`** | `snapshot_download(local_files_only=True)` raises | Check `e.snapshot_path` for partial files; re-download |
| **Multiple cache dirs** | Users set both `HF_HOME` and `HF_HUB_CACHE` inconsistently | `HF_HUB_CACHE` takes precedence over `HF_HOME` for hub data |
| **Backup includes HF cache** | Huge backup sizes | `CACHEDIR.TAG` auto-excludes it from modern backup tools |
| **Changing `HF_HOME` mid-session** | Libraries can't find models | Set at environment start; Transformers/Datasets cache independently |

## Workflow: Reclaim Disk Space

```bash
# 1. See what's cached
hf cache ls --sort size:desc

# 2. Identify stale revisions (>90 days since last access)
hf cache ls --filter "accessed>90d" --revisions

# 3. Prune unreferenced + incomplete
hf cache prune --dry-run
hf cache prune -y

# 4. Delete specific old repos
hf cache rm $(hf cache ls --filter "accessed>180d" -q) --dry-run
hf cache rm $(hf cache ls --filter "accessed>180d" -q) -y

# 5. Or programmatically in Python
python3 -c "
from huggingface_hub import scan_cache_dir
cache = scan_cache_dir()
old_revisions = [
    r for repo in cache.repos
    for r in repo.revisions
    if r.last_modified < 1700000000  # older than ~Nov 2023
]
if old_revisions:
    strategy = cache.delete_revisions(*[r.commit_hash for r in old_revisions])
    print(f'Would free {strategy.expected_freed_size_str}')
    strategy.execute()
"
```

## Verification Checklist

- [ ] Cache location matches `HF_HUB_CACHE` or `HF_HOME`/hub
- [ ] `hf cache ls` lists all cached repos with correct sizes
- [ ] `scan_cache_dir()` returns structured data without errors
- [ ] Symlinks work: `ls -la snapshots/<hash>/` shows `-> ../../blobs/<hash>`
- [ ] `try_to_load_from_cache()` returns paths for cached files, `None` for uncached
- [ ] `hf cache verify` passes for a cached model
- [ ] `delete_revisions().execute()` frees the expected space
- [ ] `hf cache prune` removes unreferenced revisions
- [ ] `CACHEDIR.TAG` exists in the cache root

## Reference

- **Docs — Understand caching:** https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache
- **Docs — Cache system reference:** https://huggingface.co/docs/huggingface_hub/en/package_reference/cache
- **Docs — Environment variables:** https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables
- **Docs — Hub local cache:** https://huggingface.co/docs/hub/en/repositories-local-cache
- **hf CLI reference:** https://huggingface.co/docs/huggingface_hub/en/guides/cli
- **Python API:** `huggingface_hub.scan_cache_dir`, `huggingface_hub.cached_assets_path`, `huggingface_hub.try_to_load_from_cache`
- **GitHub source:** https://github.com/huggingface/huggingface_hub
