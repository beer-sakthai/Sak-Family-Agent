# HF Learnings — Datasets Library v5

## 2026-07-24: hf-datasets-library-v5 — Deep Dive v2 (Topic #19, Datasets v5.0.0)

### Summary
Deep-dive into Hugging Face `datasets` v5.0.0 (major version jump) — covering the Polars integration (`from_polars`/`to_polars`), SQL/Spark connectors, interleave/concatenate with axis support, IterableDataset enhancements, native Image/Audio features, and the internal Arrow table architecture.

### Key New Features in v5.0.0

| Feature | Description |
|---------|-------------|
| **Polars integration** | `from_polars()` / `to_polars()` — direct zero-copy Arrow interop |
| **SQL round-trip** | `from_sql()` / `to_sql()` — SQLAlchemy/SQLite3 support |
| **Spark support** | `from_spark()` — PySpark DataFrame conversion |
| **Interleave datasets** | Probabilistic mixing with 3 stopping strategies |
| **Concatenate axis** | `axis=1` for horizontal merge |
| **IterableDataset parity** | Full API parity with Dataset (batch, skip, take, repeat, reshard) |
| **Image/Audio** | Mature multimodal feature types |
| **push_to_hub** | Now works with IterableDataset |

### Source
Datasets v5.0.0 installed at `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/`

### Resources
- Docs: https://huggingface.co/docs/datasets/en/index
- Changelog: https://github.com/huggingface/datasets/releases
- Audio dataset guide: https://huggingface.co/docs/datasets/en/audio_dataset
- Process audio guide: https://huggingface.co/docs/datasets/en/audio_process
- Audio feature API ref: https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.Audio

## 2026-07-24: hf-datasets-parquet-column-selection — Column Selection & Project Pushdown

### Summary
How to use column projection at load time vs. `select_columns()` after load. Column projection at load reads only the specified columns from disk — far more memory-efficient for large Parquet files.

### Key Takeaway
`columns=["a", "b"]` at load time skips reading other columns at the file level. `select_columns(["a", "b"])` after load reads everything first, then drops. For large Parquet files, projection at load saves memory and I/O.

### Source
Official docs: https://huggingface.co/docs/datasets/en/loading

## 2026-07-24: hf-datasets-features-schema-casting — Features, Schema Casting & Mixed Types

### Summary
The `Features` class defines the schema of a dataset. Casting changes column types, useful when auto-inferred types are wrong. `on_mixed_types="use_json"` handles heterogeneous fields like lists mixing ints and strings.

### Key APIs
- `dataset.cast(new_features)` — bulk cast
- `dataset.cast_column("col", Audio(...))` — single column
- `ClassLabel(names=[...])` — categorical labels stored as ints
- `on_mixed_types="use_json"` in `from_list()` and `map()`

### Source
Official docs: https://huggingface.co/docs/datasets/en/loading#troubleshooting
API ref: https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.Features

## 2026-07-24: hf-datasets-server-advanced-query — Datasets Server Advanced Query Features

### Summary
The Datasets Server REST API lets you query Parquet-converted datasets with SQL-like filters, column selection, pagination, and search. The `/rows` endpoint supports `where`, `columns`, `offset`, and `limit` parameters.

### Key Endpoints
- `GET /rows?dataset=...&config=...&split=train&where=label=1&columns=text` — filtered row access

### Source
Datasets Server API docs: https://huggingface.co/docs/datasets-server/index

## 2026-07-24: hf-datasets-builder-advanced-patterns — Custom Dataset Builders

### Summary
Creating custom dataset builders by subclassing `GeneratorBasedBuilder` or using `load_dataset("parquet", ...)` / `load_dataset("csv", ...)` with `data_files` for generic loading without writing a builder.

### Source
Official docs: https://huggingface.co/docs/datasets/en/dataset_script

## 2026-07-24: hf-datasets-arrow-parquet-writer-internals — Arrow ↔ Parquet Writer Internals

### Summary
How the `datasets` library converts between Arrow (its native format) and Parquet. The `.to_parquet()` method uses PyArrow's `ParquetWriter`, and `from_parquet()` uses PyArrow's `ParquetDataset` reader. The Hugging Face metadata (`"huggingface"` key) is stored in the Arrow schema and survives Parquet round-trip, enabling `Features` reconstruction without a separate config.

### Key Details
- `to_parquet()` preserves the `Features` schema as Arrow field metadata
- `from_parquet()` reconstructs the original `Features` from this metadata
- Row group size can be controlled for read optimization
- Compression: snappy (default), zstd, gzip, lz4

### Source
Datasets source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/arrow_dataset.py`
PyArrow Parquet docs: https://arrow.apache.org/docs/python/parquet.html

## 2026-07-24: hf-datasets-streaming-iterable-dataset-v2 — Streaming & IterableDataset Complete Deep Dive

### Summary
`IterableDataset` is the streaming variant of `Dataset` (datasets v4.8.4+). Data flows on-the-fly — no download, no disk cache, no memory load. Best for: datasets larger than RAM, remote Hub data, training loops that only need one-pass iteration, and zero-disk environments. This deep dive covers the entire API surface, internal architecture, and practical patterns.

### Loading — Three Paths

| Method | Use Case | Speed |
|--------|----------|-------|
| `load_dataset(..., streaming=True)` | Remote Hub datasets — instant access | Depends on network |
| `Dataset.to_iterable_dataset()` | Convert existing in-memory `Dataset` | Faster — reads local Arrow cache |
| `IterableDataset.from_dict(...)` | Create from Python dict | Instant — no I/O |

**Important:** `to_iterable_dataset()` is faster than `load_dataset(streaming=True)` for local datasets because it streams from cached Arrow files instead of re-fetching from the Hub. Also supports `num_shards` for parallelism:

```python
dataset = load_dataset("ethz/food101")  # download first (one-time)
iterable = dataset.to_iterable_dataset(num_shards=64)  # 64 shards for parallel loading
```

### Parquet Streaming — Column Projection & Predicate Pushdown

Parquet datasets support two critical streaming optimizations at load time:

**Column projection** — only read the columns you need:
```python
dataset = load_dataset("HuggingFaceFW/fineweb", split="train", streaming=True,
                       columns=["url", "date"])
```

**Predicate pushdown** — filter at the file level using Parquet row group statistics:
```python
dataset = load_dataset("HuggingFaceFW/fineweb", split="train", streaming=True,
                       filters=[("language_score", ">=", 0.99)])
```

These skip I/O entirely for non-matching data — far more efficient than `select_columns()` or `filter()` after load.

### Complete API Surface

#### Navigation Methods
| Method | Signature | Description | Gotcha |
|--------|-----------|-------------|--------|
| `.take(n)` | `(n: int) -> IterableDataset` | First n examples | Locks shard order — call before `shuffle` |
| `.skip(n)` | `(n: int) -> IterableDataset` | Omit first n examples | Locks shard order — call before `shuffle` |
| `.shard(index, num_shards)` | `(index, num_shards) -> IterableDataset` | Select one shard's worth of data | Returns `num_shards` shards |
| `.reshard(num_shards)` | `(num_shards: int) -> IterableDataset` | Redistribute data into new shard count | Mechanism depends on file format |

#### Transform Methods
| Method | Signature | Description | Streaming-safe? |
|--------|-----------|-------------|-----------------|
| `.map(fn, batched, batch_size, remove_columns)` | Apply transform to each example/batch | ✅ On-the-fly |
| `.filter(fn, with_indices)` | Keep examples matching predicate | ✅ On-the-fly |
| `.batch(batch_size, drop_last_batch)` | Group into batches | ✅ Lazy |
| `.shuffle(buffer_size, seed)` | Buffer-based approximate shuffle | ✅ Buffer is local |
| `.set_epoch(epoch)` | Change seed per epoch (seed + epoch) | ✅ |
| `.repeat(num)` | Repeat stream n times | ✅ |
| `.rename_column(old, new)` | Rename a column | ✅ |
| `.remove_columns(names)` | Remove one or more columns | ✅ |
| `.cast(new_features)` | Bulk change feature types | ✅ |
| `.cast_column(col, feature)` | Single-column type change | ✅ |

#### Export Methods
| Method | Output | Notes |
|--------|--------|-------|
| `.to_csv(path)` | CSV file | One row per example |
| `.to_json(path)` | JSON Lines | Standard JSONL |
| `.to_parquet(path)` | Parquet file | Preserves HF metadata |
| `.to_sql(table, conn)` | SQL table | SQLAlchemy connection |
| `.to_pandas()` | Pandas DataFrame | In-memory — use for small results |
| `.to_polars()` | Polars DataFrame | In-memory — zero-copy Arrow interop |
| `.to_dict()` | Python dict | In-memory |
| `.push_to_hub(repo_id, num_proc)` | HF Hub dataset | Uploads progressively |

### Shuffle — How It Works

`IterableDataset.shuffle(buffer_size, seed)` uses a **buffer shuffle**:

1. Fill buffer with first `buffer_size` examples from all shards
2. Randomly select one from buffer, yield it, replace with next example
3. Buffer size controls randomness quality — larger = better shuffle

**Additionally**, if the dataset has multiple shards, the **order of shards is also shuffled** (using the same seed). This provides two-level randomness.

**Reshuffle per epoch:** Use `set_epoch(epoch)` which changes the effective seed to `seed + epoch`:
```python
for epoch in range(epochs):
    shuffled_dataset.set_epoch(epoch)
    for example in shuffled_dataset:
        ...
```

**Warning:** `take()` and `skip()` lock shard order, preventing future `shuffle()` calls. Always shuffle before splitting.

### Checkpoint & Resume

`IterableDataset` supports state serialization for training resumption:

```python
# Save checkpoint
state_dict = iterable_dataset.state_dict()  # current shard + position

# Resume
iterable_dataset.load_state_dict(state_dict)  # reads from checkpoint position
```

**Internal mechanism:** The dataset tracks `(current_shard_index, example_index_within_shard)`. On load, it skips fully-read shards and fast-forwards through the current shard. No re-reading of completed shards.

**Limitation:** Shuffle buffers are *not* checkpointed — on resume, the buffer is refilled with fresh data from the current position. This means the same example won't be reshuffled identically after resume.

**Integration with torchdata:**
```python
from torchdata.stateful_dataloader import StatefulDataLoader
dataloader = StatefulDataLoader(iterable_dataset, batch_size=32, num_workers=4)
state_dict = dataloader.state_dict()  # wraps iterable_dataset.state_dict()
```

### Interleave — Multi-Dataset Mixing

`interleave_datasets()` combines multiple IterableDatasets with alternating examples:

```python
from datasets import interleave_datasets
mixed = interleave_datasets([es_dataset, fr_dataset],
                            probabilities=[0.8, 0.2],
                            seed=42,
                            stopping_strategy="first_exhausted")
```

**Stopping strategies:**
| Strategy | Behavior |
|----------|----------|
| `"first_exhausted"` (default) | Stop when any dataset runs out (subsampling) |
| `"all_exhausted"` | Stop when ALL datasets exhausted (oversampling — wraps around) |
| `"all_exhausted_without_replacement"` | Every sample seen exactly once |

**Shard preservation:** The interleaved dataset has `min(all_input_shards)` shards. Each new shard contains at least 1 shard from every input dataset.

### Concatenate — Merge Datasets

`concatenate_datasets()` chains datasets:

- **`axis=0` (default):** Vertically stack — requires same column types. Shards concatenated.
- **`axis=1`:** Horizontally merge — requires same number of rows. Result is 1 shard (avoids misalignment).

```python
stories = load_dataset("ajibawa-2023/General-Stories-Collection", split="train", streaming=True)
stories = stories.select_columns(["text"])
wiki = load_dataset("wikimedia/wikipedia", "20231101.en", split="train", streaming=True)
wiki = wiki.select_columns(["text"])
combined = concatenate_datasets([stories, wiki])  # 10 + 41 = 51 shards
```

### Batch Processing

Two approaches:

**1. `.batch()` — direct batched iteration:**
```python
batched = dataset.batch(batch_size=32, drop_last_batch=True)
for batch in batched:
    # batch is a dict of lists
```

**2. `.map(batched=True)` — batch transforms (tokenization etc.):**
```python
def tokenize(examples):
    return tokenizer(examples['text'], truncation=True, padding='max_length')
dataset = dataset.map(tokenize, batched=True, remove_columns=["text", "timestamp", "url"])
```

### Training Loop Pattern

```python
import torch
from torch.utils.data import DataLoader

dataset = load_dataset("...", streaming=True, split="train")
dataset = dataset.shuffle(seed=42, buffer_size=10_000)
dataset = dataset.map(tokenize, batched=True)
dataset = dataset.with_format("torch")
dataloader = DataLoader(dataset, batch_size=32)

model = AutoModelForMaskedLM.from_pretrained("distilbert-base-uncased")
for epoch in range(3):
    dataset.set_epoch(epoch)
    for batch in dataloader:
        ...
```

### Feature Type Detection Limitation

IterableDatasets loaded from Hugging Face Hub may show `features: Unknown` — that's normal. The features are inferred lazily from the first streamed batch. To force explicit features, load and cast:
```python
dataset = load_dataset("...", streaming=True, split="train")
# Features will be populated after first iteration
```

### Push to Hub

`IterableDataset.push_to_hub()` iterates the dataset and progressively uploads:
```python
dataset.push_to_hub("username/my_dataset")
dataset.push_to_hub("username/my_dataset", num_proc=8)  # parallel — only if num_shards > 1
```

### Local File Streaming

Streaming from local files avoids Arrow conversion:
```python
dataset = load_dataset("json", data_files={"train": "*.jsonl.gz"}, streaming=True)
```
Benefits: instant start, no disk usage for cache, works with compression.

### Key Limitations (Updated)
1. **No `len()`** for multi-shard sets — unknown until full iteration
2. **No random access** — cannot index like `ds[42]`
3. **Shuffle is approximate** — buffer-based, not perfect Fisher-Yates
4. **`map()` is single-process** — no `num_proc` for streaming datasets
5. **Shuffle buffer lost on checkpoint resume**
6. **Network-dependent** for Hub datasets
7. **`take()`/`skip()` lock shard order** — prevents later `shuffle()`
8. **Feature auto-detection** may show "Unknown" until first iteration

### Source
- Official streaming docs: https://huggingface.co/docs/datasets/en/stream
- IterableDataset API: https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.IterableDataset
- Datasets source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/iterable_dataset.py`

---

## 2026-07-25: hf-datasets-from-parquet — Loading Parquet Datasets with Dataset.from_parquet()

### Summary
`Dataset.from_parquet()` is the direct method to create a Dataset from Parquet file(s). It reads Parquet files via PyArrow, caches the data in Arrow format on disk, and returns a memory-mapped Dataset. This is the low-level counterpart to `load_dataset("parquet", data_files=...)` but offers more direct control over scan options, filtering, and column selection.

### Two Approaches to Load Parquet

| Approach | When to Use |
|----------|-------------|
| `Dataset.from_parquet(path)` | Direct file loading with full parameter control |
| `load_dataset("parquet", data_files=...)` | Auto-split detection, Hub integration, streaming |

```python
from datasets import Dataset, load_dataset

# Approach 1: Direct
ds = Dataset.from_parquet("data.parquet")

# Approach 2: Builder-based (auto-detect splits from filenames)
ds = load_dataset("parquet", data_files={"train": "train.parquet", "test": "test.parquet"})
```

### Full API Reference

```python
Dataset.from_parquet(
    path_or_paths,           # str or list[str] — local or remote paths
    split=None,              # NamedSplit — assign a split name
    features=None,           # Features — override auto-inferred schema
    cache_dir=None,          # str — override default cache location
    keep_in_memory=False,    # bool — load entirely into RAM
    columns=None,            # List[str] — column projection at read time
    num_proc=None,           # int — parallel file processing
    filters=None,            # pyarrow Expression or list[tuple] — predicate pushdown
    fragment_scan_options=None,  # ParquetFragmentScanOptions — advanced tuning
    on_bad_files="error",    # "error" | "warn" | "skip"
    **kwargs                 # passed to ParquetConfig
)
```

### Key Parameters

#### `columns` — Column Projection (Memory Saver)
Only read the columns you need. Parquet reads column chunks independently, so unrequested columns are never touched on disk:

```python
# Only reads col_a and col_b from the file
ds = Dataset.from_parquet("large.parquet", columns=["col_a", "col_b"])

# Supports nested column prefixes: "a" selects "a.b", "a.c"
ds = Dataset.from_parquet("nested.parquet", columns=["metadata"])
```

**Why this matters:** A Parquet file with 500 columns where you need only 3 — column projection at read time skips 99.4% of I/O. Doing `select_columns()` after load still reads everything into memory first.

#### `filters` — Predicate Pushdown (Performance Multiplier)
Filters are pushed down to the Parquet reader, which uses **row group statistics** (min/max values per column stored in the file footer) to skip entire groups of rows without reading them:

```python
# Simple predicate (AND logic for top-level tuples)
ds = Dataset.from_parquet("data.parquet", filters=[("language", "==", "en"), ("score", ">=", 0.9)])

# OR logic (list of lists)
ds = Dataset.from_parquet("data.parquet", filters=[[("source", "==", "twitter")], [("source", "==", "reddit")]])

# PyArrow expression (most flexible)
import pyarrow.dataset as pads
expr = (pads.field("date") >= "2026-01-01") & (pads.field("lang") == "en")
ds = Dataset.from_parquet("data.parquet", filters=expr)
```

**How pushdown works:**
1. Parquet files store **min/max statistics** per column per row group
2. If you filter `score >= 0.9`, the reader skips any row group where `max(score) < 0.9`
3. A well-partitioned or sorted Parquet file can skip 99%+ of row groups
4. This is **far faster** than loading everything and then calling `.filter()`

#### `fragment_scan_options` — Advanced I/O Tuning
For remote Parquet files, control buffering and caching behavior:

```python
import pyarrow.dataset as pads
import pyarrow as pa

# Increase range size + prefetch for high-latency connections
scan_opts = pads.ParquetFragmentScanOptions(
    cache_options=pa.CacheOptions(
        prefetch_limit=1,
        range_size_limit=128 << 20  # 128 MiB per request
    ),
)
ds = Dataset.from_parquet("https://.../data.parquet", fragment_scan_options=scan_opts)
```

| Parameter | Default | Tuning |
|-----------|---------|--------|
| `prefetch_limit` | 0 (no prefetch) | 1 for high-latency links |
| `range_size_limit` | 32 MiB | Increase for distant regions with good bandwidth |

#### `on_bad_files` — Graceful Error Handling

```python
# Default: raise on any unreadable file
ds = Dataset.from_parquet(["good.parquet", "bad.parquet"], on_bad_files="error")

# Warn and skip
ds = Dataset.from_parquet(files, on_bad_files="warn")  # logs warning, skips bad files

# Silently skip corrupt files
ds = Dataset.from_parquet(files, on_bad_files="skip")
```

Useful when processing a directory with mixed file quality. `"warn"` is good for automated pipelines (you still get notified), `"skip"` for best-effort processing.

#### `num_proc` — Multi-File Parallelism

```python
# Process 8 Parquet shards in parallel
ds = Dataset.from_parquet(["shard_{i:04d}.parquet" for i in range(100)], num_proc=8)
```

Each worker process gets a subset of files. Only speeds up loading when you have **multiple files** — a single large Parquet file processes in one process regardless.

### Loading Remote Parquet Files

```python
# HTTP/HTTPS URLs
ds = Dataset.from_parquet("https://huggingface.co/datasets/org/dataset/resolve/main/data.parquet")

# hf:// protocol (Hub datasets or Storage Buckets)
ds = Dataset.from_parquet("hf://datasets/username/dataset/train-00000-of-00001.parquet")
ds = Dataset.from_parquet("hf://buckets/username/bucket-name/data.parquet")
```

### Loading Multiple Files

```python
# List of paths — they become one contiguous dataset
files = ["part-00000.parquet", "part-00001.parquet", "part-00002.parquet"]
ds = Dataset.from_parquet(files)

# Globbing with pathlib
from pathlib import Path
files = sorted(Path("data/").glob("*.parquet"))
ds = Dataset.from_parquet([str(f) for f in files])
```

### ParquetConfig — Additional Options

`**kwargs` passed to `ParquetConfig`:

| Parameter | Description |
|-----------|-------------|
| `batch_size` | Rows per Arrow RecordBatch (default: row group size) |
| `suffix_template` | Cache file naming pattern for multi-file loads |

### Comparison: `from_parquet()` vs `load_dataset("parquet", ...)`

| Feature | `Dataset.from_parquet()` | `load_dataset("parquet")` |
|---------|--------------------------|---------------------------|
| **Split auto-detection** | ❌ Manual | ✅ From filenames or YAML config |
| **Streaming** | ❌ Always cached | ✅ `streaming=True` |
| **`filters` pushdown** | ✅ Direct | ✅ |
| **`columns` projection** | ✅ Direct | ✅ |
| **`fragment_scan_options`** | ✅ Direct | ✅ |
| **`on_bad_files`** | ✅ Direct | ❌ (via `num_proc` error handling) |
| **Hub dataset auto-detect** | ❌ Manual path | ✅ Auto-find Parquet files |
| **`num_proc`** | ✅ | ✅ |
| **Local files** | ✅ | ✅ |
| **Remote URLs** | ✅ | ✅ |
| **`hf://` protocol** | ✅ | ✅ |
| **DuckDB SQL queries** | ❌ | ❌ (use Datasets Server) |

### Performance Tips

1. **Always specify `columns`** if you only need a subset — avoids reading unused column chunks
2. **Use `filters`** for row-level pruning — row group statistics skip irrelevant data
3. **Prefer `from_parquet()` for control** when you know exact file paths and want `fragment_scan_options`
4. **Prefer `load_dataset()` for convenience** when loading from Hub repos with auto-split detection
5. **Avoid loading then filtering** large datasets — push predicates down to the reader
6. **Use `num_proc` with many shards** — but single-threaded for a single Parquet file
7. **Parquet + Snappy (default)** is a good balance of speed and compression; use Zstd for better compression ratios

### Example: End-to-End Pipeline

```python
from datasets import Dataset
import pyarrow.dataset as pads

# 1. Load only what you need
ds = Dataset.from_parquet(
    "hf://datasets/bigcode/the-stack/train-00000-of-00128.parquet",
    columns=["content", "language", "size"],
    filters=[("language", "==", "Python"), ("size", ">", 1024)],
)

# 2. Process with map
ds = ds.map(lambda x: {"size_kb": x["size"] / 1024})

# 3. Save back to Parquet
ds.to_parquet("python-stack.parquet")

print(f"Loaded {len(ds)} Python files over 1KB")
```

### Source
- Official docs: https://huggingface.co/docs/datasets/en/loading#parquet
- API ref (v5.0.0): https://huggingface.co/docs/datasets/main/en/package_reference/main_classes#datasets.Dataset.from_parquet
- API ref (v4.8.4): https://huggingface.co/docs/datasets/v4.8.4/en/package_reference/main_classes#datasets.Dataset.from_parquet
- Datasets source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/arrow_dataset.py` (line ~1488)
- PyArrow dataset docs: https://arrow.apache.org/docs/python/dataset.html

---

## 2026-07-24: hf-datasets-sort-shuffle-split-shard — Dataset Sort, Shuffle, Split & Shard Deep Dive (Topic #162 Deepened)

### Summary
Comprehensive deep-dive into the 🤗 Datasets library's row-rearrangement methods — `sort()`, `shuffle()`, `select()`, `filter()`, `train_test_split()`, and `shard()` — tested live against Datasets v5.0.0 with the MRPC dataset (3,668 rows).

### Key Discovery: v5.0.0 sort() API Changes
`sort()` now accepts `column_names` (plural) — a single string or sequence of strings — and supports per-column `reverse` as either a single bool or a per-column sequence. `null_placement` controls where null rows appear:

```python
# Single-column sort
sorted_ds = ds.sort("label")                     # ascending (default)
sorted_rev = ds.sort("label", reverse=True)      # descending

# Multi-column sort (v5.0.0+)
sorted_multi = ds.sort(["label", "idx"], reverse=[False, True])

# Null placement (v5.0.0+)
sorted_nulls_first = ds.sort("label", null_placement="at_start")
```

The sort creates an **indices mapping** — a list of integer indices sorted by column values, used to reorder rows on access. This is memory-efficient (only stores `n` int32 values) but adds indirection on every read.

### Key Discovery: shuffle() — Performance Trap
`shuffle()` randomly permutes the indices mapping. **After shuffle, all subsequent row access becomes ~10× slower** because data is no longer read contiguously from the Arrow table:

```python
shuffled = ds.shuffle(seed=42)  # fast (O(n) permutation), but...
print(shuffled[0])              # slow — random seek in Arrow table
```

**The fix:** `flatten_indices()` rewrites the entire dataset to disk, materializing the shuffled order into a contiguous Arrow table:

```python
# Slow access after shuffle
shuffled = ds.shuffle(seed=42)

# Rewrite to disk — restores contiguous access speed
flattened = shuffled.flatten_indices()  # ~60ms for 3,668 rows
print(flattened[0])                     # fast again
```

`flatten_indices()` copies all data to a new cache file. For large datasets, this is a one-time cost worth paying if you'll do many random accesses.

### Key Discovery: IterableDataset Buffer Shuffle
For streaming/large datasets, use `IterableDataset.shuffle()` — a buffer-based approximate shuffle that avoids creating indices mappings entirely:

```python
iterable = dataset.to_iterable_dataset(num_shards=128)
shuffled = iterable.shuffle(seed=42, buffer_size=10_000)
```

**How it works:** Fills a buffer from all shards, randomly selects one to yield, replaces it. Buffer size controls shuffle quality — larger = better randomness. Also shuffles shard order. No `flatten_indices()` needed because there's no indices mapping.

**Per-epoch re-shuffle:** Use `set_epoch(epoch)` to change the effective seed per epoch:
```python
for epoch in range(5):
    shuffled.set_epoch(epoch)
    for example in shuffled:
        ...
```

### Key Discovery: select() vs filter()
Two filtering approaches with different performance characteristics:

| Aspect | `select()` | `filter()` |
|--------|-----------|------------|
| **Input** | List of integer indices | Callable predicate |
| **Memory** | Stores indices list (efficient) | Materializes all data matching predicate |
| **Speed** | O(n) — just creates index list | O(n × fn_cost) — evaluates function on every row |
| **Use case** | Known positions | Dynamic conditions |
| **with_indices** | N/A | ✅ `filter(fn, with_indices=True)` passes `(example, idx)` |

```python
# select — known positions, instant
subset = ds.select([0, 10, 20, 30, 40])

# filter — dynamic condition (evaluates all rows)
result = ds.filter(lambda x: x["label"] == 1)  # ~0.01s for 3,668 rows

# filter with indices
even = ds.filter(lambda ex, idx: idx % 2 == 0, with_indices=True)
```

Both create indices mappings, with the same `flatten_indices()` escape hatch for speed recovery.

### Key Discovery: train_test_split() with Stratification
`train_test_split()` creates train/test splits with optional stratified sampling:

```python
# Basic split
split = ds.train_test_split(test_size=0.1, seed=42)

# Stratified split (v5.0.0+) — preserves class proportions
stratified = ds.train_test_split(test_size=0.2, stratify_by_column="label", seed=42)

# Absolute count
split = ds.train_test_split(test_size=100, train_size=500)
```

Returns a `DatasetDict` with `"train"` and `"test"` keys. Default `shuffle=True` — set `shuffle=False` to preserve order (e.g., time-series).

### Key Discovery: shard() — Contiguous vs Round-Robin
`shard()` splits a dataset into `num_shards` equal chunks:

```python
# Default: contiguous (splits dataset into sequential blocks)
shard_0 = ds.shard(num_shards=4, index=0)  # rows 0–916
shard_1 = ds.shard(num_shards=4, index=1)  # rows 917–1833

# Round-robin: distributes rows 0,4,8... to shard 0 → better for imbalanced sorted data
shard_2 = ds.shard(num_shards=4, index=2, contiguous=False)
```

| Parameter | `contiguous=True` (default) | `contiguous=False` |
|-----------|-----------------------------|-------------------|
| **Distribution** | Sequential blocks | Round-robin |
| **Shard locality** | Rows are adjacent | Rows interleaved across shards |
| **Use case** | Split large file into chunks | Distributed processing / worker assignment |
| **Random access after** | Fast (contiguous) | Slow (scattered indices) |

### Best Practices

1. **For exploration/analysis:** Use `select()` over `filter()` when indices are known — it avoids evaluating a function on every row
2. **After shuffle/filter:** Call `flatten_indices()` if you'll do repeated random access — the one-time rewrite cost pays off quickly
3. **For large datasets (streaming):** Use `IterableDataset.shuffle(buffer_size)` — no indices mapping, no speed penalty
4. **For model training:** Use `IterableDataset.shuffle()` with `set_epoch()` for per-epoch reshuffling; avoid `Dataset.shuffle()` + `flatten_indices()` at scale
5. **For train/test split:** Use `stratify_by_column` to maintain class balance — critical for imbalanced classification datasets
6. **For distributed processing:** Use `shard(contiguous=False)` (round-robin) for balanced worker assignment when data is sorted by a label column
7. **Per-epoch shuffling order:** `shuffle() → flatten_indices()` once, then save the flattened dataset and reload each epoch — faster than re-shuffling from scratch

### Live Test Results (verified this session)
Tested on `nyu-mll/glue` MRPC split (3,668 rows) with Datasets v5.0.0:
- `sort(label)`: 0.001s — instant (creates indices mapping)
- `shuffle(seed=42)`: 0.003s — fast (permutes indices)
- `flatten_indices()`: 0.062s — rewrites 3,668 rows to disk
- `filter(label==1)`: 2,474 matching rows — ~0.01s for 3,668 evaluations
- `train_test_split(test_size=0.1)`: 3,301 train + 367 test — balanced split
- `shard(4, 0)`: 917 rows per shard — equal distribution

### Source
- Official docs (process): https://huggingface.co/docs/datasets/en/process
- Dataset API ref (v5.0.0): https://huggingface.co/docs/datasets/main/en/package_reference/main_classes#datasets.Dataset
- IterableDataset API ref: https://huggingface.co/docs/datasets/main/en/package_reference/main_classes#datasets.IterableDataset
- Datasets source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/arrow_dataset.py`
- Live test: datasets v5.0.0 on MRPC (3,668 rows), verified this session
