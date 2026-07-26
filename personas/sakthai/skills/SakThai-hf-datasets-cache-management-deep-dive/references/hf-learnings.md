# HF Learning: Datasets Cache Management Deep Dive

**Learned:** 2026-07-25  
**Topic:** `hf-datasets-cache-management-deep-dive`  
**Author:** SakThai

## Summary

Deep dive into the Hugging Face Datasets library's Arrow-backed cache architecture. The `datasets` library maintains two caching layers: the Hub cache (`~/.cache/huggingface/hub`) for raw source files, and the Datasets Arrow cache (`~/.cache/huggingface/datasets`) for converted Arrow tables. Understanding this architecture is critical for managing disk space, optimizing performance, and troubleshooting cache-related issues.

## Key Learnings

### Architecture
- The datasets library uses **Apache Arrow** as its on-disk format, which supports memory-mapped zero-copy reads
- `Dataset.map()` outputs are cached separately from the base dataset — each map creates a new cache-<hash>.arrow file
- The fingerprinting system deterministically identifies cache entries: function bytecode, input state hash, args, and batched/batch_size/remove_columns all factor in
- Cache invalidation is automatic when the function or input state changes (hash mismatch)

### Environment Variables Hierarchy
- `HF_HOME` sets the root for all HF caches (models, datasets, hubs, tokenizers)
- `HF_DATASETS_CACHE` overrides specifically the datasets cache location
- `HF_HUB_CACHE` overrides specifically the Hub download cache
- `HF_DATASETS_IN_MEMORY_MAX_SIZE` moves data from disk cache to RAM for speed
- **Gotcha**: Setting `HF_DATASETS_CACHE` without `HF_HUB_CACHE` can cause unexpected behavior because the Hub cache is still at the default location

### Performance Tuning
- Memory mapping provides near-instant loading after the first conversion
- In-memory mode (IN_MEMORY_MAX_SIZE > 0) is the fastest option for datasets that fit in RAM
- Streaming mode uses zero disk but has no random access — use it for large datasets or quick exploration
- Converting a `Dataset` to `IterableDataset` via `.to_iterable_dataset()` is faster than loading with `streaming=True` because it streams from local Arrow files

### Cache Management
- `dataset.cleanup_cache_files()` removes orphaned Arrow cache files safely
- `download_mode='force_redownload'` ensures a completely fresh copy
- `load_from_cache_file=False` in Dataset.map() forces re-execution of transforms
- `disable_caching()` is a global toggle for all map caching
- The Hub cache can be managed via `huggingface-cli delete-cache` or programmatically with `scan_cache()` from `huggingface_hub`

### Hub vs Datasets Cache Distinction
- The **Hub cache** stores raw files by their hash (content-addressable), with refs/snapshots/blobs structure
- The **Datasets cache** stores Arrow tables in a per-dataset/per-split/per-config hierarchy
- They serve different purposes and don't interfere, but share disk space under `~/.cache/huggingface/`

## Practical Recipes

### Move cache to a temp directory for disposable workloads
```bash
export HF_DATASETS_CACHE=/tmp/hf-datasets-cache
export HF_HUB_CACHE=/tmp/hf-hub-cache
python my_script.py
rm -rf /tmp/hf-datasets-cache /tmp/hf-hub-cache
```

### Per-experiment isolation
```python
dataset = load_dataset("my/dataset", cache_dir=f"./cache/experiment-{run_id}")
```

### Check cache size
```bash
du -sh ~/.cache/huggingface/datasets
du -sh ~/.cache/huggingface/hub
```

### Programmatic Hub cache scan
```python
from huggingface_hub import scan_cache_dir
scan = scan_cache_dir()
for repo in scan.repos:
    print(f"{repo.repo_id}: {repo.size_on_disk}")
```

## Sources
- Official docs: https://huggingface.co/docs/datasets/en/cache
- Source: https://raw.githubusercontent.com/huggingface/datasets/main/docs/source/cache.mdx
- Hub cache management: https://huggingface.co/docs/huggingface_hub/guides/manage-cache
