---
name: SakThai-hf-datasets-library
author: SakThai
license: MIT
title: Hugging Face Datasets Library
category: mlops
tags: [datasets, arrow, memory-mapping, cache, map, processing, data-loading]
related_skills:
  - hf-datasets-server-rest-api
description: Deep dive into the Hugging Face `datasets` Python library — Arrow-backed memory mapping, caching architecture, Dataset.map() operations, and processing pipelines.
version: 1.0.0
---

# Hugging Face Datasets Library Deep Dive

The `datasets` library is Hugging Face's high-performance data processing layer. Built on Apache Arrow, it provides memory-mapped access to large datasets with zero-copy reads, enabling manipulation of terabyte-scale data on machines with limited RAM.

## Architecture — Arrow Backend

Apache Arrow is the foundation:

- **Columnar memory layout** — column-oriented for fast slicing and queries
- **Zero-copy reads** — virtually no serialization overhead
- **Language-agnostic** — works across Python, C++, Java, etc.
- **Memory-mapped from disk** — data stays on disk; only metadata and accessed pages load into RAM
  - Example: 18 GB Wikipedia dataset loads in ~50 MB RAM
  - Iteration speed: ~4.8 Gb/s on a standard laptop
- **Native integrations** — zero-copy hand-offs to NumPy, Pandas, PyTorch, TensorFlow, JAX

## Cache System

Two independent caches:

| Cache | Default Location | Purpose |
|-------|-----------------|---------|
| Hub cache | `~/.cache/huggingface/hub` | Raw downloaded files (models, tokenizers, datasets) |
| Arrow cache | `~/.cache/huggingface/datasets` | Processed datasets in Arrow format |

Environment variables:
- `HF_HOME=/path/to/cache_root` — moves everything (`datasets` + `hub` subdirs)
- `HF_DATASETS_CACHE=/path/to/arrow_cache` — datasets-specific only
- `HF_HUB_CACHE=/path/to/hub_cache` — hub downloads only

Loading control:
```python
# Per-call cache directory
dataset = load_dataset('username/dataset', cache_dir="/path/to/cache")

# Force redownload
dataset = load_dataset('rajpurkar/squad', download_mode='force_redownload')

# Load dataset in-memory for speed
# Set datasets.config.IN_MEMORY_MAX_SIZE to a byte value (e.g., 2GB = 2*1024**3)
# Or env var: HF_DATASETS_IN_MEMORY_MAX_SIZE=2147483648

# Disable caching globally
from datasets import disable_caching
disable_caching()

# Skip cache for a specific map() call
dataset.map(my_function, load_from_cache_file=False)

# Clean up old Arrow cache files
dataset.cleanup_cache_files()
```

## Indices Mapping Performance

Critical performance concept: operations like `sort()`, `shuffle()`, `select()`, and `filter()` create an **indices mapping** — a list mapping logical row index to physical row index in the Arrow table.

- **Without indices mapping**: sequential reads, maximal throughput
- **With indices mapping**: random access through indirection, ~10x slower
- **Fix**: call `Dataset.flatten_indices()` to rewrite the entire dataset to disk and remove the indirection
- **Alternative**: use `IterableDataset.shuffle()` for approximate fast shuffling without indices mapping

## Core Processing API

### Row Operations

```python
# Sort by column values (creates indices mapping)
sorted_ds = dataset.sort("label")

# Shuffle (creates indices mapping)
shuffled = dataset.shuffle(seed=42)

# Select by index list (creates indices mapping)
small = dataset.select([0, 10, 20, 30])

# Filter (creates indices mapping)
even = dataset.filter(lambda ex, idx: idx % 2 == 0, with_indices=True)

# Train/test split
train_test = dataset.train_test_split(test_size=0.1)

# Shard into N pieces
shard_0 = dataset.shard(num_shards=4, index=0)
```

### Column Operations

```python
# Rename
ds = dataset.rename_column("sentence1", "sentenceA")

# Remove columns
ds = dataset.remove_columns(["sentence1", "sentence2"])
ds = dataset.select_columns(["idx", "label"])  # inverse of remove

# Cast feature types
from datasets import ClassLabel, Value
new_features = dataset.features.copy()
new_features["label"] = ClassLabel(names=["neg", "pos"])
new_features["idx"] = Value("int64")
ds = dataset.cast(new_features)

# Single column cast
ds = dataset.cast_column("audio", Audio(sampling_rate=16000))

# Flatten nested structures
flat = dataset.flatten()
# answers: {text: [...], answer_start: [...]} → answers.text, answers.answer_start
```

### Dataset.map() — The Workhorse

`.map()` is the core processing method. Its 20+ parameters control everything from parallelism to caching.

```python
# Simple per-example
def add_prefix(example):
    example["sentence1"] = "Prefix: " + example["sentence1"]
    return example
updated = dataset.map(add_prefix)

# Remove columns during map
updated = dataset.map(lambda ex: {"new": ex["sentence1"]}, remove_columns=["sentence1"])
```

### DatasetDict.map()

Apply to all splits simultaneously:

```python
dataset = load_dataset('nyu-mll/glue', 'mrpc')
encoded = dataset.map(lambda examples: tokenizer(examples["sentence1"]), batched=True)
# Applies to both train and test splits
```

### Map Configuration Deep Dive

#### `batched` + `batch_size`

```python
# Per-example (default)
dataset.map(my_fn)                          # batch_size=1, batched=False

# Batched — process N examples at once
dataset.map(my_fn, batched=True)            # batch_size=1000 (default)
dataset.map(my_fn, batched=True, batch_size=500)  # tune for memory
dataset.map(my_fn, batched=True, batch_size=-1)   # whole dataset as one batch

# Drop incomplete final batch
dataset.map(my_fn, batched=True, drop_last_batch=True)

# Pass specific columns as positional args
dataset.map(my_fn, batched=True, input_columns=["text", "label"])
```

**Batch size tuning:**
- **Smaller** (< 500) — lower memory per step, good for GPU tokenization
- **Larger** (> 5000) — higher throughput for CPU-bound work
- `batch_size=-1` or `None` — single batch (entire dataset), risky for memory
- `drop_last_batch=True` — ensures uniform batch sizes; use when output size must match input size

#### `num_proc` — Parallel Multiprocessing

```python
dataset.map(my_fn, num_proc=4)              # 4 parallel workers
dataset.map(my_fn, num_proc=os.cpu_count()) # use all cores
```

**Requirements:**
- Function **must be picklable** — define at module top level, not inside another function or class
- Lambda functions are NOT picklable — use `def` for `num_proc > 1`
- Uses Python's `multiprocessing` under the hood (the `multiprocess` fork for better pickle support)
- Each worker gets a **subset of shards** (not individual rows) — datasets are split by Arrow file shards
- `num_proc` applies to `.map()`, `.filter()`, `Dataset.from_generator()`, and dataset loading

**Memory:**
- Each worker process is a separate Python process — memory usage scales linearly with `num_proc`
- Arrow memory-mapped files are **shared** across processes (no copy), so the base data doesn't duplicate
- But intermediate results and the function's memory footprint duplicate per worker

**Suffix template** — controls cache file naming with multiple workers:

```python
dataset.map(my_fn, num_proc=4, suffix_template="_{rank:05d}_of_{num_proc:05d}")
# Produces: processed_00001_of_00004.arrow, processed_00002_of_00004.arrow, ...
```

#### `with_rank` — Multi-GPU / Distributed Processing

```python
# Distribute GPU work across processes
def gpu_computation(batch, rank):
    device = f"cuda:{(rank or 0) % torch.cuda.device_count()}"
    model.to(device)
    ...
    return batch

# Must use spawn start method for CUDA
from multiprocess import set_start_method
set_start_method("spawn")
updated = dataset.map(gpu_computation, batched=True, batch_size=16,
                       with_rank=True, num_proc=torch.cuda.device_count())
```

The `rank` parameter gives each worker its process index (0 to `num_proc-1`).

#### `fn_kwargs` — Pass Extra Keyword Arguments

```python
def my_fn(example, model_name="default", threshold=0.5):
    ...
    return example

dataset.map(my_fn, fn_kwargs={"model_name": "bert", "threshold": 0.8})
```

Cleaner than wrapping in a lambda. Works with multiprocessing since the function is a top-level `def`.

#### `writer_batch_size` — Cache File Write Buffer

```python
dataset.map(my_fn, writer_batch_size=1000)   # default
dataset.map(my_fn, writer_batch_size=100)    # lower memory, more writes
dataset.map(my_fn, writer_batch_size=10000)  # fewer writes, higher peak memory
```

Controls how many rows are buffered in memory before flushing to the Arrow cache file:
- **Higher** → fewer I/O operations, faster processing, more peak RAM
- **Lower** → gentler memory profile, slower due to more flushes
- Range: 100–10000 is typical. Default 1000 is a good general trade-off.

#### `try_original_type` and `on_mixed_types`

```python
# Preserve original Arrow types (e.g., int32 stays int32)
dataset.map(my_fn, try_original_type=True)   # default

# Auto-infer types from mapped output
dataset.map(my_fn, try_original_type=False)

# Handle mixed-type fields (lists with strings + ints, dicts with arbitrary values)
dataset.map(my_fn, on_mixed_types="use_json")
```

`try_original_type=True` (default) preserves the input column's data type when the output has the same schema. `on_mixed_types="use_json"` (v4.7.0+) stores heterogeneous data as JSON strings in Arrow, enabling storage of fields without a fixed schema.

#### `with_indices` — Use Example Indices in Processing

```python
# Pass the index to your function
dataset.map(lambda ex, idx: {"id": idx, **ex}, with_indices=True)

# Can combine with rank for distributed processing
dataset.map(lambda ex, idx, rank: {...}, with_indices=True, with_rank=True, num_proc=4)
```

Signature when both enabled: `function(example, idx, rank)` — index first, then rank.

### Asynchronous Processing (API Calls)

When your `map` function is `async def`, the datasets library runs it concurrently:

```python
import aiohttp, asyncio
from huggingface_hub import get_token

sem = asyncio.Semaphore(20)  # rate limit — default max is 1000

async def query_model(model, prompt):
    api_url = f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {get_token()}"}
    json_data = {"messages": [{"role": "user", "content": prompt}], "max_tokens": 20}
    async with sem, aiohttp.ClientSession() as session, session.post(api_url, headers=headers, json=json_data) as response:
        output = await response.json()
        return {"Output": output["choices"][0]["message"]["content"]}

async def get_topic(example):
    return await query_model(model, prompt.format(Problem=example['Problem']))

ds = ds.map(get_topic)  # runs up to 1000 parallel async tasks
```

**Async map rules:**
- Default concurrency: **1000 simultaneous calls** — use `asyncio.Semaphore(N)` to rate-limit
- Works with both `batched=True` and `batched=False`
- Does NOT work with `num_proc` (async is single-process, event-loop-based)
- Best for I/O-bound work: API calls, database queries, file reads
- The event loop runs in the main process — no pickling needed

### Caching Behavior with map

```python
# Force recompute
dataset.map(my_fn, load_from_cache_file=False)

# Provide custom cache file path
dataset.map(my_fn, cache_file_name="/path/to/custom_cache.arrow")

# Process entirely in memory (no cache file written)
dataset.map(my_fn, keep_in_memory=True)

# With multiple processes
dataset.map(my_fn, num_proc=4, cache_file_name="processed.arrow")
# Creates: processed_00001_of_00004.arrow, ..., processed_00004_of_00004.arrow
```

**Cache fingerprinting:** The library computes a hash (fingerprint) of the dataset state + transform arguments + function source code. If the fingerprint matches an existing cache file, it loads from cache. Changes to the function (even whitespace) change the fingerprint.

**When caching goes wrong:**
1. Function uses external state (random seed, timestamp, global variable) → fingerprint doesn't capture this → stale results
2. Fix: set `load_from_cache_file=False` for non-deterministic functions
3. Or: pass explicit `new_fingerprint` to bypass fingerprint computation

## Dataset Composition

```python
from datasets import concatenate_datasets, interleave_datasets

### Concatenate
# Vertical (same columns, more rows)
combined = concatenate_datasets([ds1, ds2])

# Horizontal (same rows, more columns)
combined = concatenate_datasets([ds1, ds2], axis=1)

### Interleave (mix datasets)
ds = interleave_datasets(
    [d1, d2, d3],
    probabilities=[0.3, 0.5, 0.2],
    seed=42,
    stopping_strategy="first_exhausted"  # or "all_exhausted", "all_exhausted_without_replacement"
)
```

## On-the-fly Format Conversion

```python
# PyTorch tensors
dataset = dataset.with_format("torch")

# NumPy
dataset = dataset.with_format("numpy")

# Pandas DataFrame (zero-copy)
dataset = dataset.with_format("pandas")

# Polars
dataset = dataset.with_format("polars")

# Custom transform (e.g., tokenization)
def encode(batch):
    return tokenizer(batch["sentence1"], padding="longest", truncation=True, return_tensors="pt")
dataset = dataset.with_transform(encode)

# Reset to original
dataset = dataset.with_format(None)
```

## Persistence

```python
# Local (Arrow — fast reload, large files)
dataset.save_to_disk("path/to/dataset")
reloaded = load_from_disk("path/to/dataset")

# Hub (Parquet — smaller, slower reload)
dataset.push_to_hub("username/my_dataset")
dataset.push_to_hub("username/my_dataset", num_proc=8)  # parallel upload
reloaded = load_dataset("username/my_dataset", streaming=True)

# Export formats
dataset.to_csv("file.csv")
dataset.to_json("file.json")
dataset.to_parquet("file.parquet")
dataset.to_sql("table_name", connection)
dataset.to_pandas()
dataset.to_dict()
```

## Streaming Mode

Use `streaming=True` in `load_dataset()` for datasets too large for local storage:

```python
ds = load_dataset("bigcode/the-stack", split="train", streaming=True)
for example in ds:
    process(example)
```

## Parquet-Optimized Loading

When working with Parquet datasets (the default format on the Hub), the `datasets` library exposes Apache Arrow's predicate pushdown and column projection directly. These can **dramatically** reduce I/O and memory.

### Column Projection at Load Time

Use `columns` to load **only the columns you need**. The Parquet reader skips entire column chunks at the file level — vastly more memory-efficient than loading everything then calling `select_columns()`:

```python
# ❌ Loads ALL columns into memory, then drops most
ds = load_dataset("bigcode/the-stack", split="train", streaming=True)
ds = ds.select_columns(["content"])  # data for other columns was already read

# ✅ Only reads the 'content' column from disk
ds = load_dataset("bigcode/the-stack", split="train", streaming=True,
                  columns=["content"])

# Works with regular (non-streaming) loading too — Parquet column statistics
# allow skipping entire column chunks during read
ds = load_dataset("my-dataset", split="train", columns=["col_0", "col_1"])
```

**When to use each approach:**
| Approach | Data read | Memory | Best for |
|----------|-----------|--------|----------|
| `columns=["a"]` at load | Only column `a` | Minimal | Non-streaming, large Parquet files |
| `select_columns(["a"])` after load | All columns, then filtered | Higher | After computation, small datasets |

### Filter Pushdown (Predicate Pushdown)

Filters are pushed to the Parquet reader, which uses **row group statistics** (min/max values per column) to skip entire groups of rows:

```python
# Only rows where language_score >= 0.99 — skipping can happen at row group level
ds = load_dataset("my-dataset", streaming=True,
                  filters=[("language_score", ">=", 0.99)])

# Compound filters (AND logic by default for top-level tuples)
ds = load_dataset("my-dataset", streaming=True,
                  filters=[("language", "==", "en"), ("length", ">", 100)])

# OR logic (list of lists)
ds = load_dataset("my-dataset", streaming=True,
                  filters=[[("source", "==", "twitter"), ("source", "==", "reddit")]])

# With explicit pyarrow expression
import pyarrow.dataset as ds_expr
ds = load_dataset("my-dataset", streaming=True,
                  filters=(ds_expr.field("language_score") >= 0.99))

# Combine with column projection for maximum efficiency
ds = load_dataset("my-dataset", streaming=True,
                  columns=["url", "date"],
                  filters=[("date", ">=", "2026-01-01")])
```

**Performance impact:** With Parquet row group metadata, a filter on an integer column can skip 99%+ of row groups without reading any data from them. This is far faster than loading everything then calling `.filter()`.

### Batch Size Tuning for Parquet

Control the number of rows per RecordBatch (defaults to the row group size):

```python
# Default: row group size (typically 1M–10M rows)
ds = load_dataset("my-dataset", streaming=True)

# Smaller batches for memory-constrained environments
ds = load_dataset("my-dataset", streaming=True, batch_size=10_000)

# Larger batches for throughput
ds = load_dataset("my-dataset", streaming=True, batch_size=1_000_000)
```

### fragment_scan_options — Streaming Performance Tuning

Control buffering, caching, and prefetch for remote Parquet files (especially useful for slow connections):

```python
import pyarrow.dataset as ds_expr
import pyarrow as pa

# 128 MiB range size + prefetch 1 fragment ahead
scan_opts = ds_expr.ParquetFragmentScanOptions(
    cache_options=pa.CacheOptions(
        prefetch_limit=1,
        range_size_limit=128 << 20  # 128 MiB minimum request
    ),
)
ds = load_dataset("my-dataset", streaming=True,
                  fragment_scan_options=scan_opts)
```

**Trade-offs:**
| `prefetch_limit` | `range_size_limit` | Effect |
|-----------------|-------------------|--------|
| 0 (no prefetch) | 32MiB (default) | Minimal memory, slower on high-latency links |
| 1 | 128MiB | Good for distant regions (fewer, larger requests) |
| 2+ | 256MiB+ | High throughput, higher peak memory |

### Bad File Handling

Some Parquet datasets contain corrupted files. Control how to handle them:

```python
# Skip bad files without error
ds = load_dataset("my-dataset", on_bad_files="skip")

# Warn on bad files but continue
ds = load_dataset("my-dataset", on_bad_files="warn")

# Default: raise on bad files
ds = load_dataset("my-dataset", on_bad_files="error")
```

## Pitfalls

> **Complementary skill**: [`hf-datasets-server-rest-api`](..) covers the Datasets Server REST API — exploring, searching, and filtering datasets on the Hub without downloading. Use it for quick data inspection before deciding what to load locally.

1. **Indices mapping kills performance** — after `sort()`, `shuffle()`, `filter()`, `select()`, call `flatten_indices()` or the dataset iterates ~10× slower
2. **Cache collisions** — if you modify processing functions, set `load_from_cache_file=False` or `disable_caching()` to avoid stale results
3. **Multi-GPU requires spawn** — `set_start_method("spawn")` needed for CUDA in subprocesses
4. **Rate limits on async map** — default 1000 concurrent queries; always use `asyncio.Semaphore`
5. **`HF_HUB_CACHE` ≠ `HF_DATASETS_CACHE`** — they are separate; setting one doesn't set the other
6. **In-place mutation doesn't work** — all processing methods return a new `Dataset` object; modifications are not in-place
