---
name: SakThai-hf-hub-cache-system-deep-dive
description: "Complete deep-dive on the Hugging Face Hub local cache system \u2014 file-based cache\
  \ architecture (blobs, refs, snapshots, trees, .no_exist), Xet chunk-based deduplication,\
  \ asset caching for downstream libraries, cache inspection/verification/cleanup\
  \ via"
---

# HF Hub Cache System — Deep Dive

## Overview

The Hugging Face Hub cache system is a local disk caching layer shared across all HF libraries (Transformers, Datasets, Diffusers, etc.). It prevents re-downloading files across revisions and repos, saves bandwidth, and accelerates model/dataset loading.

**Two cache layers:**

| Layer | Purpose | Location |
|-------|---------|----------|
| **File-based cache** | Caches individual files by content hash | `~/.cache/huggingface/hub/` |
| **Xet chunk-based cache** | Deduplicates byte-range chunks (64 KB) | `~/.cache/huggingface/xet/` |

Both layers are fully integrated — standard APIs (`hf_hub_download`, `snapshot_download`, Transformers `from_pretrained`) use them transparently.

## Cache Directory Structure

### Default locations

| Env var | Default | Purpose |
|---------|---------|---------|
| `HF_HOME` | `~/.cache/huggingface` | Root for all HF cache data |
| `HF_HUB_CACHE` | `$HF_HOME/hub` | File-based cache |
| `HF_ASSETS_CACHE` | `$HF_HOME/assets` | Downstream library assets |
| `HF_HOME`/xet | `$HF_HOME/xet` | Xet chunk cache |

Set any via environment variable or pass `cache_dir=` to individual methods.

### File-based cache tree

```
~/.cache/huggingface/hub/
├── models--<user>--<repo>/       # Each cached repo
│   ├── refs/
│   │   └── main                  # Branch → commit hash mapping
│   ├── blobs/
│   │   ├── <sha256-hash>         # Actual file content (content-addressed)
│   │   └── ...
│   ├── snapshots/
│   │   ├── <commit-hash>/        # One folder per revision
│   │   │   ├── README.md         # Symlink → ../../blobs/<hash>
│   │   │   ├── config.json       # Symlink → ../../blobs/<hash>
│   │   │   └── ...
│   │   └── ...
│   ├── trees/
│   │   ├── <commit-hash>.json    # Cached file listing per commit
│   │   └── ...
│   └── .no_exist/                # (Optional) files known not to exist
│       └── <commit-hash>/
│           └── optional_config_that_does_not_exist.json  # Empty marker
├── datasets--<user>--<repo>/     # Same structure for datasets
├── spaces--<user>--<repo>/       # Same structure for Spaces
└── CACHEDIR.TAG                  # Marks dir as exclude-from-backup
```

### Naming convention

Repo folder names encode type, namespace, and name with `--` separators:

| Repo | Cache folder |
|------|-------------|
| `bert-base-uncased` (model, no namespace) | `models--bert-base-uncased` |
| `julien-c/EsperBERTo-small` (model) | `models--julien-c--EsperBERTo-small` |
| `glue` (dataset, no namespace) | `datasets--glue` |
| `huggingface/DataMeasurementsFiles` (dataset) | `datasets--huggingface--DataMeasurementsFiles` |
| `dalle-mini/dalle-mini` (Space) | `spaces--dalle-mini--dalle-mini` |

## Core Architecture

### Refs

Maps branch/tag names to current commit hashes. Updated only when a new commit is fetched for that reference.

```
refs/main  →  "bbc77c8132af1cc5cf678da3f1ddf2de43606d48"
```

### Blobs

Content-addressed storage. Each file is stored once by its SHA-256 hash. Identical files across revisions or even across repos share the same blob — zero extra disk cost.

### Snapshots

Symlink forests. Each revision gets its own snapshot folder; files inside are symlinks pointing to `../../blobs/<hash>`. This lets you:
- See a coherent file tree for any revision
- Share identical files across revisions (same hash = same blob)
- Keep old revisions indefinitely without extra storage

### Trees

Cache of repository file listings per commit. Stored as JSON files. Avoids a network call per file when downloading a known commit.

### .no_exist

Tracks files known not to exist on the Hub (to avoid repeated 404 lookups). Contains empty marker files — negligible disk usage.

### CACHEDIR.TAG

Auto-generated at `~/.cache/huggingface/`. Follows the [Cache Directory Tagging Standard](https://bford.info/cachedir/). Tells backup tools (Borg, restic, rsync) to skip this directory.

## Managing the Cache — CLI

All commands use the `hf cache` subcommand.

### `hf cache ls` — Inspect

```bash
# List all cached repos
hf cache ls

# Output:
# ID                                   SIZE   LAST_ACCESSED LAST_MODIFIED REFS
# ------------------------------------ ------ ------------- ------------- -------------------
# dataset/glue                         116.3K 4 days ago     4 days ago     2.4.0 main 1.17.0
# model/bert-base-cased                  1.9G 1 week ago     2 years ago
# model/t5-small                        970.7M 3 days ago     3 days ago     main refs/pr/1
# Found 6 repo(s) for a total of 12 revision(s) and 3.4G on disk.

# Show per-revision breakdown
hf cache ls --revisions

# Filter by size or access time
hf cache ls --filter "size>1GB" --filter "accessed>30d"

# JSON/CSV output for scripting
hf cache ls --format json
hf cache ls --format csv

# Quiet mode — just IDs, one per line (for piping to rm)
hf cache ls --quiet

# Sort and limit
hf cache ls --sort size:desc --limit 10
```

### `hf cache rm` — Delete

```bash
# Delete an entire repo
hf cache rm model/bert-base-cased

# Delete specific revision by hash
hf cache rm 8f3ad1c

# Mix repos and revisions
hf cache rm model/t5-small 8f3ad1c

# Dry-run to preview
hf cache rm model/t5-small --dry-run

# Skip confirmation (for scripts)
hf cache rm model/t5-small --yes

# Pipe from ls for bulk cleanup
hf cache rm $(hf cache ls --filter "accessed>1y" -q) -y

# Custom cache directory
hf cache rm model/gpt2 --cache-dir /mnt/cache/huggingface/hub
```

### `hf cache prune` — Garbage Collection

```bash
# Delete unreferenced revisions + incomplete downloads
hf cache prune

# Output:
# About to delete 3 unreferenced revision(s) and 2 incomplete download(s) (2.4G total).
#   - model/t5-small:
#       1c610f6b [refs/pr/1] 820.1M
#       d4ec9b72 [(detached)] 640.5M
#   - dataset/google/fleurs:
#       2b91c8dd [(detached)] 937.6M
# Proceed? [y/N]: y
# Deleted 3 unreferenced revision(s) and 2 incomplete download(s); freed 2.4G.

# Non-interactive
hf cache prune -y

# Preview only
hf cache prune --dry-run
```

**What `prune` removes:**
- Revisions not referenced by any branch or tag (detached commits)
- `.incomplete` files — partial blobs from interrupted downloads

**What `prune` does NOT remove:**
- Revisions still referenced by a branch, tag, or PR ref
- Entire repos (use `rm` for that)

### `hf cache verify` — Integrity Check

```bash
hf cache verify meta-llama/Llama-3.2-1B-Instruct
# ✅ Verified 13 file(s) ... All checksums match.

# Verify specific revision
hf cache verify meta-llama/Llama-3.1-8B-Instruct --revision 0e9e39f249a16976918f6564b8830bc894c89659
```

## Managing the Cache — Python API

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
