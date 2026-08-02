---
name: SakThai-hf-datasets-cache-management-deep-dive
author: SakThai
license: MIT
title: HF Datasets Cache Management
category: mlops
tags: [datasets, cache, arrow, memory-mapping, performance, streaming, disk-management]
related_skills:
  - hf-datasets-library
  - hf-hub-cache-deep-dive
  - hf-datasets-streaming-iterable-dataset
  - hf-huggingface-hub-download-lifecycle
description: Deep dive into the Hugging Face Datasets library's Arrow-backed cache architecture — how datasets are cached on disk, memory-mapped for zero-copy access, and how to manage, optimize, and troubleshoot the cache.
version: 1.0.0
---

# HF Datasets Cache Management

## Overview

The `datasets` library maintains **two separate caching layers**:

1. **Hub cache** (`~/.cache/huggingface/hub`) — managed by `huggingface_hub`, stores raw downloaded files (Parquet, JSONL, etc.)
2. **Datasets Arrow cache** (`~/.cache/huggingface/datasets`) — stores converted Arrow tables, indices, and processed outputs

This skill focuses on the **Datasets Arrow cache** — its architecture, management, and performance tuning.

## Key Concepts

### Arrow Cache
When you call `load_dataset()`, the library:
1. Downloads raw source files into the Hub cache (if not cached)
2. Converts them into Apache Arrow format
3. Writes Arrow files to the datasets cache directory
4. Memory-maps those Arrow files for near-zero-copy access

Subsequent loads skip re-downloading AND re-converting — they just memory-map the existing Arrow files.

### Memory Mapping
Datasets uses PyArrow's memory mapping (`pa.memory_map()`) to load cached Arrow files. This means:
- No separate deserialization step — data is accessed directly from disk via virtual memory
- Multiple processes can share the same mapped memory pages
- OS handles paging; frequently accessed data stays in RAM, cold data stays on disk

### Cache File Structure
Each split's processed output is stored as:
```
~/.cache/huggingface/datasets/
  <dataset_name>/
    <config>/
      <split>/
        dataset.arrow          # The main Arrow table
        dataset.arrow.mmap     # Index file for memory mapping
        cache-<hash>.arrow     # Cached outputs from Dataset.map()
        state.json             # Processing state metadata
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `HF_HOME` | Root for all HF caches | `~/.cache/huggingface` |
| `HF_DATASETS_CACHE` | Datasets-specific cache dir | `~/.cache/huggingface/datasets` |
| `HF_HUB_CACHE` | Hub download cache dir | `~/.cache/huggingface/hub` |
| `HF_DATASETS_IN_MEMORY_MAX_SIZE` | Max bytes for in-memory cache | `0` (disabled) |
| `HF_DATASETS_OFFLINE` | Disable network access | unset |

### Precedence
- `HF_DATASETS_CACHE` overrides `HF_HOME/datasets`
- `HF_HUB_CACHE` overrides `HF_HOME/hub`
- `HF_HOME` is the broadest — sets both datasets and hub caches

## Download Modes

`load_dataset(download_mode=...)` controls cache behavior:

| Mode | Behavior |
|------|----------|
| `reuse_dataset_if_exists` (default) | Use cached if present |
| `force_redownload` | Re-download and re-convert |
| `reuse_cache_if_exists` | Re-download raw files but reuse Arrow cache |

Use `force_redownload` when the source dataset has been updated or you need a clean copy.

## Cache Control in Dataset.map()

### Per-call control
```python
dataset = dataset.map(my_function, load_from_cache_file=False)
```
When `True` (default), if a cached output exists for the same function + args + dataset state, it's loaded from cache instead of re-executed. Set to `False` to force re-execution.

### Global toggle
```python
from datasets import disable_caching()
# All subsequent map() calls re-execute
```

### Cache invalidation
The cache key is a hash of:
- The function's bytecode
- The function's `__code__.co_code`
- Input dataset fingerprint
- `batched`, `batch_size`, `remove_columns`, `input_columns`, `fn_kwargs`

Change any of these and a new cache entry is created automatically.

## Cache Cleanup

### Per-dataset
```python
cleaned = dataset.cleanup_cache_files()
# Returns number of removed files
```

### Full cleanup
```bash
rm -rf ~/.cache/huggingface/datasets
# Or scoped to a specific dataset:
rm -rf ~/.cache/huggingface/datasets/<namespace>__<dataset_name>
```

### Automated cleanup strategies
1. Set `HF_DATASETS_CACHE` to a tempdir for disposable workloads
2. Use `download_mode='force_redownload'` periodically to refresh
3. Monitor cache size with `du -sh ~/.cache/huggingface/datasets`

## In-Memory Caching for Performance

For small-to-medium datasets, disabling the Arrow cache and loading entirely in memory speeds up all operations significantly.

```python
import datasets
datasets.config.IN_MEMORY_MAX_SIZE = 2 * 1024**3  # 2GB
```

Or via environment:
```bash
export HF_DATASETS_IN_MEMORY_MAX_SIZE=2000000000
```

When set:
- Dataset loads directly into RAM instead of Arrow files
- No disk I/O for subsequent operations
- All `map()`, `filter()`, `select()` etc. operate on in-memory data
- **Tradeoff**: RAM usage scales with dataset size

## Streaming vs Cache

| Approach | Disk Usage | First Load | Repeated Access | Random Access |
|----------|-----------|------------|-----------------|---------------|
| Classic (cached) | High (Arrow + Hub) | Slow (download + convert) | Instant (memory-mapped) | Full |
| Streaming | None | Instant (first row) | Same as first | Not supported |
| In-memory | None (RAM) | Same as classic | Fastest | Full |

## Best Practices

1. **Shared environments**: Set `HF_DATASETS_CACHE` to a shared volume (NFS, etc.) but watch for concurrent write conflicts
2. **CI/CD**: Use `download_mode='force_redownload'` in CI to ensure fresh data
3. **Large datasets**: Prefer streaming; convert to Arrow cache only for repeated-access workloads
4. **Experiments**: Set a unique `cache_dir` per experiment to avoid cache poisoning between runs
5. **Memory mapping**: On memory-constrained systems, keep the cache on SSD for fast memory-mapped reads
6. **Cache size**: Periodically monitor with `huggingface-cli delete-cache` (for Hub cache) or `du -sh` (for datasets cache)

## Reference

- [Datasets Cache Docs](https://huggingface.co/docs/datasets/en/cache)
- [Hub Cache Management](https://huggingface.co/docs/huggingface_hub/guides/manage-cache)
- [huggingface_hub scan_cache() API](https://huggingface.co/docs/huggingface_hub/v0.27/en/package_reference/caching)
