---
name: sakthai-hf-snapshot-download-and-cache-management
description: "Hugging Face Hub: snapshot_download, cache locations, revision locking, and disk-space management."
version: 1.0.0
author: SakThai
license: MIT
tags: [huggingface, hf, hub, snapshot_download, cache, data-management]
platforms: [linux, macos, windows]
---

# Hugging Face Hub: snapshot_download and Cache Management

This skill explains how Hugging Face Hub caching works, how to control where files land, and how to manage disk usage when working with large models or datasets.

## Overview

- The `huggingface_hub` Python library caches every downloaded model, dataset, or Space on disk.
- `snapshot_download()` is the canonical, framework-agnostic way to pull a repository revision into the local cache.
- Cache behavior is controlled by environment variables, the `cache_dir` argument, and revision pinning.

## Default Cache Locations

| OS | Default Path |
|----|---------------|
| Linux | `~/.cache/huggingface/hub` |
| macOS | `~/Library/Caches/huggingface/hub` |
| Windows | `C:\Users\<USER>\.cache\huggingface\hub` |

- Set `HF_HOME` to override the root; `HF_HUB_CACHE` overrides only the `hub/` subdirectory.
- Example: `HF_HOME=/mnt/data/hf_cache` keeps everything on a mounted volume.

## snapshot_download in Practice

```python
from huggingface_hub import snapshot_download

# Latest revision
local_dir = snapshot_download(
    repo_id="bert-base-uncased",
    repo_type="model",
)

# Specific Git revision (commit SHA, branch, or tag)
local_dir = snapshot_download(
    repo_id="bert-base-uncased",
    revision="main",
)

# Subset of files only
local_dir = snapshot_download(
    repo_id="bert-base-uncased",
    allow_patterns=["*.json", "tokenizer.*"],
)
```

- Returns the absolute path to the downloaded snapshot.
- If the revision is already cached, it resolves instantly (hardlinks or copies from cache).

## Cache Internals

- Repositories are stored as snapshots keyed by revision SHA.
- Files are deduplicated across snapshots when possible: identical blobs share a single physical copy underneath `blobs/`.
- A `refs/` folder stores branch and tag pointers to revision SHAs.

## Disk Management

```python
from huggingface_hub import scan_cache_dir

info = scan_cache_dir()
print(f"Size: {info.size_on_disk / 1e9:.2f} GB")
```

- `scan_cache_dir()` returns cached repos, last accessed times, and blob sizes.
- `delete_revisions()` and `delete_cache()` let you prune safely without breaking other snapshots.

## LFS Awareness

- Large files (weights, audio, images) use Git LFS pointers; `snapshot_download` fetches the real LFS content transparently.
- `huggingface-cli repo-info <id> --repo-type model` shows LFS file counts before downloading.
- For very large models, consider `max_workers` and `local_dir` to keep downloads on a fast drive.

## Transfer-Layer Deduplication (XET)

- `huggingface_hub >= 1.2.2` uses the **XET** protocol for uploads and downloads. XET performs **chunk-based deduplication** on the wire: identical chunks across different files are transferred and stored only once. See the `hf-xet` skill.
- This is separate from on-disk cache deduplication: XET reduces network traffic and backend storage; the `blobs/` cache still deduplicates identical files locally.

## Key Facts

- `snapshot_download` is revision-safe: storing the commit SHA guarantees reproducibility even if upstream branches move.
- Cache deduplication means disk impact is usually far smaller than the sum of repo sizes when multiple models share weights.
- `HF_HOME`, `HF_HUB_CACHE`, and `TRANSFORMERS_CACHE` / `HF_ASSETS_CACHE` can be combined to route models, tokenizer assets, and datasets to different disks.
- Deletion is soft by design: you can prune snapshots or blobs without removing metadata for other working copies.
- `allow_patterns` / `ignore_patterns` in `snapshot_download` make it practical to fetch only config and tokenizer files for inspection.
