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

## 2026-07-24: hf-datasets-concatenate-and-interleave-deep-dive — Combining Datasets

> Research date: 2026-07-24
> Docs: https://huggingface.co/docs/datasets/en/process
> Author: SakThai · Main Lead of the House & Master of Hugging Face
> License: MIT

### Summary

🤗 Datasets provides two primary functions for combining datasets:
- **`concatenate_datasets()`** — stack datasets vertically (append rows) or horizontally (merge columns)
- **`interleave_datasets()`** — mix datasets by alternating or probabilistically sampling examples

Both work with regular `Dataset` and `IterableDataset` (streaming) objects.

### 1. `concatenate_datasets()`

#### Vertical Concatenation (`axis=0`, default)

Stacks datasets row-wise. All datasets **must share the same column types/features** or the operation raises.

```python
from datasets import concatenate_datasets, load_dataset

stories = load_dataset("ajibawa-2023/General-Stories-Collection", split="train")
stories = stories.select_columns(["text"])

wiki = load_dataset("wikimedia/wikipedia", "20231101.en", split="train")
wiki = wiki.select_columns(["text"])

# Features must match type
assert stories.features.type == wiki.features.type

bert_dataset = concatenate_datasets([stories, wiki])
# Result: len(stories) + len(wiki) rows, same features
```

**Key invariant:** `concatenate_datasets([ds.shard(n, i) for i in range(n)])` recovers the original dataset in order.

#### Horizontal Concatenation (`axis=1`)

Merges columns side-by-side. Datasets **must have the same number of rows**:

```python
stories_ids = stories.map(lambda x, i: {"id": i}, with_indices=True)
stories_with_ids = concatenate_datasets([stories, stories_ids], axis=1)
```

#### API Signature

```python
concatenate_datasets(
    dsets: list,
    info: Optional[DatasetInfo] = None,
    split: Optional[NamedSplit] = None,
    axis: int = 0
) -> Dataset
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `dsets` | `list[Dataset]` | Datasets to concatenate (≥2) |
| `info` | `Optional[DatasetInfo]` | Override merged dataset info |
| `split` | `Optional[NamedSplit]` | Assign a named split |
| `axis` | `int` | `0`=vertical (rows), `1`=horizontal (columns) |

### 2. `interleave_datasets()`

Mixes datasets by taking alternating or probability-weighted examples. Supports three **stopping strategies**:

#### Default: Alternating (`first_exhausted`)

Without probabilities, examples are taken in round-robin order:

```python
from datasets import Dataset, interleave_datasets

d1 = Dataset.from_dict({"a": [0, 1, 2]})
d2 = Dataset.from_dict({"a": [10, 11, 12]})
d3 = Dataset.from_dict({"a": [20, 21, 22]})

dataset = interleave_datasets([d1, d2, d3])
dataset["a"]  # [0, 10, 20, 1, 11, 21, 2, 12, 22]
```

#### With Probabilities

Defines sampling weights. Each example is drawn from a random dataset according to probabilities:

```python
dataset = interleave_datasets(
    [d1, d2, d3],
    probabilities=[0.7, 0.2, 0.1],
    seed=42
)
```

With `first_exhausted` (default): stops as soon as any dataset runs out — this is a **subsampling** strategy. Result length ≤ min(dataset lengths).

#### Stopping Strategies

| Strategy | Behaviour |
|----------|-----------|
| `first_exhausted` (default) | Stop when *any* dataset runs out. Subsampling. |
| `all_exhausted` | Continue until every sample from every dataset has been seen at least once. **Oversampling** — exhausted datasets wrap around. |
| `all_exhausted_without_replacement` | Every sample seen exactly once. Equal to alternating if sizes match. |

**`all_exhausted` example:**

```python
# d1=3 rows, d2=4 rows, d3=5 rows
dataset = interleave_datasets([d1, d2, d3], stopping_strategy="all_exhausted")
# Cycles through shorter datasets until all have been fully consumed
```

#### With IterableDataset (Streaming)

```python
es_dataset = load_dataset('allenai/c4', 'es', split='train', streaming=True)
fr_dataset = load_dataset('allenai/c4', 'fr', split='train', streaming=True)

multilingual = interleave_datasets([es_dataset, fr_dataset])
# Alternates: es, fr, es, fr, ...

# With probabilities + oversampling:
multilingual = interleave_datasets(
    [es_dataset, fr_dataset],
    probabilities=[0.8, 0.2],
    seed=42,
    stopping_strategy="all_exhausted"
)
```

#### Sharding Behaviour

When using sharding with interleaved IterableDatasets, the interleaved dataset's shard count = **minimum** of input shard counts. Each new shard contains at least 1 shard from every input dataset:

```
Input shards:  [32, 48, 128]
Interleaved:   min = 32 shards
Per new shard: 1 from ds1, 1-2 from ds2, 4 from ds3
```

#### API Signature

```python
interleave_datasets(
    datasets: list,
    probabilities: Optional[list[float]] = None,
    seed: Optional[int] = None,
    info: Optional[DatasetInfo] = None,
    split: Optional[NamedSplit] = None,
    stopping_strategy: Literal[
        'first_exhausted',
        'all_exhausted',
        'all_exhausted_without_replacement'
    ] = 'first_exhausted'
) -> Dataset | IterableDataset
```

### 3. Key Differences

| Aspect | `concatenate_datasets()` | `interleave_datasets()` |
|--------|------------------------|------------------------|
| Data flow | All of A, then all of B | Alternating/probabilistic |
| Row count | Sum of all inputs | Varies by strategy |
| Column requirement | Same types (axis=0) or same rows (axis=1) | Same types |
| Dataset types | `Dataset` only | `Dataset` + `IterableDataset` |
| Probabilities | No | Yes |
| Stopping strategies | N/A | 3 strategies |
| Use case | Training on combined corpora | Multi-domain balanced training, language mixing |

### 4. Practical Patterns

**Multi-language training:** Use `interleave_datasets()` with probabilities to control language distribution:

```python
datasets = [load_dataset(..., lang, split="train", streaming=True) for lang in langs]
probs = [0.5, 0.3, 0.2]  # 50% English, 30% French, 20% Spanish
mixed = interleave_datasets(datasets, probabilities=probs, seed=42)
```

**Adding metadata columns:** Use `concatenate_datasets(axis=1)` to attach IDs or metadata:

```python
ds_with_ids = concatenate_datasets([original, id_dataset], axis=1)
```

**Reassembling shards:** `concatenate_datasets(shards)` recovers the original order — useful after distributed processing.

### Source
- Official process docs: https://huggingface.co/docs/datasets/en/process
- API ref: https://huggingface.co/docs/datasets/v4.8.4/en/package_reference/main_classes#datasets.concatenate_datasets
- Stream guide: https://huggingface.co/docs/datasets/en/stream
- Live test: datasets v5.0.0 on MRPC (3,668 rows), verified this session
---

## 2026-07-24: hf-datasets-from-parquet — Loading Parquet Files with `datasets` Library (Topic #149 Deepened)

### Summary
Comprehensive deep-dive into loading Parquet data with the `datasets` library (v5.0.0). Covers `Dataset.from_parquet()` (path, columns, filters, num_proc, fragment_scan_options, on_bad_files), `load_dataset()` with auto-detected parquet format, the `ParquetConfig` options (split, streaming), pyarrow filter predicate pushdown for efficient column/row pruning, multi-file loading with sharding, integration with the Datasets Server `/parquet` endpoint for server-side conversions, and practical performance patterns.

### Source
- huggingface/datasets source: `src/datasets/io/parquet.py` (ParquetDatasetReader)
- huggingface/datasets source: `src/datasets/packaged_modules/parquet/parquet.py` (Parquet builder)
- Official docs: https://huggingface.co/docs/datasets/en/parquet_processing
- API reference: https://huggingface.co/docs/datasets/v5.0.0/en/package_reference/main_classes#datasets.Dataset.from_parquet
- PyArrow Dataset docs: https://arrow.apache.org/docs/python/generated/pyarrow.dataset.ParquetFragmentScanOptions.html

### 1. `Dataset.from_parquet()` — Core API

```python
from datasets import Dataset

# Single file
ds = Dataset.from_parquet("data/train-00000-of-00001.parquet")

# Multiple files (sharded dataset)
ds = Dataset.from_parquet([
    "data/train-00000-of-00004.parquet",
    "data/train-00001-of-00004.parquet",
    "data/train-00002-of-00004.parquet",
    "data/train-00003-of-00004.parquet",
])

# Select columns only (saves I/O)
ds = Dataset.from_parquet("data.parquet", columns=["text", "label"])

# Filter rows on load — predicate pushdown to Parquet metadata
ds = Dataset.from_parquet(
    "data.parquet",
    filters=[("label", "==", 1)]       # only rows where label == 1
)

# Compound filter
ds = Dataset.from_parquet(
    "data.parquet",
    filters=[("label", "==", 1), ("split", "in", ["train", "val"])]
)

# Multi-process parsing (num_proc)
ds = Dataset.from_parquet(
    ["shard-1.parquet", "shard-2.parquet", "shard-3.parquet"],
    num_proc=3                   # one process per file
)
```

**Full parameter reference:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path_or_paths` | `PathLike \| list[PathLike]` | required | Single Parquet file path or list of paths |
| `split` | `NamedSplit` | `None` | Split name to assign (e.g., `"train"`, `"test"`) |
| `features` | `Features` | `None` | Explicit feature schema (auto-detected if None) |
| `cache_dir` | `str` | `~/.cache/huggingface/datasets` | Cache directory for Arrow data |
| `keep_in_memory` | `bool` | `False` | Copy all data in-memory instead of memory-mapping |
| `columns` | `list[str]` | `None` | Subset of columns to load (prunes at read time) |
| `num_proc` | `int` | `None` | Parallel reading across files (v2.8.0+) |
| `filters` | `Expression \| list[tuple] \| list[list[tuple]]` | `None` | Predicate pushdown filter — prunes rows at source |
| `fragment_scan_options` | `ParquetFragmentScanOptions` | `None` | Scan tuning (buffering, caching) (v4.2.0+) |
| `on_bad_files` | `"error" \| "warn" \| "skip"` | `"error"` | Behavior on unreadable files (v4.2.0+) |
| `**kwargs` | any | — | Passed to `ParquetConfig` |

### 2. Filter Predicate Pushdown — Deep Dive

Filters are evaluated at the **Parquet metadata level** — row group statistics (`min`, `max`, `null_count`) are checked before any I/O. This means entire row groups can be skipped without decompression.

**Filter format — tuple list:**
```python
# Simple: [("column", "op", value)]
filters = [("age", ">=", 18)]

# AND: multiple tuples in same list
filters = [("age", ">=", 18), ("country", "==", "US")]

# OR: list of lists (each inner list is AND-ed)
filters = [("age", ">=", 18), [("country", "==", "US"), ("country", "==", "CA")]]
# = (age >= 18) AND (country == "US" OR country == "CA")
```

**Filter format — pyarrow Expression (more expressive):**
```python
import pyarrow.dataset as pds

# Equivalent to tuple list
filt = (pds.field("age") >= 18) & (pds.field("country") == "US")

ds = Dataset.from_parquet("data.parquet", filters=filt)
```

**Supported operators:** `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`

**Performance impact:** For a 10 GB Parquet file partitioned into 64 MB row groups, a selective filter can skip 95%+ of row groups, reducing read to ~500 MB and load time from minutes to seconds.

### 3. `load_dataset()` with Parquet — Auto-Detection

`load_dataset()` automatically detects Parquet files by extension (`.parquet`):

```python
from datasets import load_dataset

# From local directory of parquet files
ds = load_dataset("parquet", data_dir="./my-data/")
# or explicitly:
ds = load_dataset("parquet", data_files="data/*.parquet")

# From Hugging Face Hub (auto-detects parquet if no loading script)
ds = load_dataset("username/my-parquet-dataset", split="train")

# Force parquet builder
ds = load_dataset(
    "parquet",
    data_files={
        "train": "train-*.parquet",
        "test": "test-*.parquet",
    }
)

# With streaming
ds = load_dataset("parquet", data_files="big.parquet", streaming=True)
```

**The auto-detection logic** (from `packaged_modules/parquet/parquet.py`):
1. When `load_dataset()` is called with a dataset path, it first checks for a loading script
2. If none found, it inspects the repo's file extensions
3. If `.parquet` files dominate, it uses the `Parquet` packaged builder
4. The builder reads file metadata (schema, row count) without loading data

### 4. Streaming Parquet Data

```python
# Streaming reads rows on-demand — no local cache
ds = load_dataset("parquet", data_files="huge.parquet", streaming=True)

# IterableDataset methods
for i, example in enumerate(ds):
    if i > 100:
        break
    print(example["text"])

# Take/skip/shuffle
sample = ds.take(1000)               # first 1000
ds_filtered = ds.filter(lambda x: x["label"] == 1)
```

**When to stream:**
- Dataset too large for available disk
- Iterating once (training epoch over large corpus)
- Exploring data before deciding to download

**When NOT to stream:**
- Multiple random-access passes needed
- Index-based lookups (`ds[5000]`)
- Shuffling before training (use `IterableDataset.shuffle()` instead)

### 5. Datasets Server `/parquet` Endpoint Integration

The Datasets Server exposes a `/parquet` endpoint that returns URLs to pre-converted Parquet files for any compatible dataset:

```python
import requests

# Get parquet URLs for a dataset
resp = requests.get(
    "https://datasets-server.huggingface.co/parquet?dataset=imdb"
)
parquet_data = resp.json()
parquet_files = parquet_data["parquet_files"]

# {'dataset': 'imdb', 'config': 'plain_text', 'split': 'train',
#  'url': 'https://.../imdb/plain_text/train/0000.parquet'}

# Load directly from URLs
ds = load_dataset(
    "parquet",
    data_files={"train": [p["url"] for p in parquet_files]},
    streaming=True
)
```

**Key `/parquet` response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `dataset` | `str` | Dataset name |
| `config` | `str` | Configuration/subset name |
| `split` | `str` | Split name |
| `url` | `str` | HTTPS URL to the Parquet file |
| `size` | `int` | File size in bytes |
| `columns` | `list[str]` | Column names in the file |

**Practical pattern — zero-cost Hub querying without downloading:**
```python
from datasets import load_dataset

# Stream a Hub dataset from its Parquet conversion
ds = load_dataset(
    "parquet",
    data_files={
        "train": [
            "https://huggingface.co/datasets/username/dataset/resolve/refs%2Fconvert%2Fparquet/train/0000.parquet"
        ]
    },
    streaming=True
)

# or use the datasets-server API for auto-discovery
import requests, json
url = "https://datasets-server.huggingface.co/parquet?dataset=username/dataset"
files = requests.get(url).json()["parquet_files"]
ds = load_dataset("parquet", data_files={"train": [f["url"] for f in files]})
```

### 6. Performance Patterns

**Pattern 1: Column selection first, filter second**
```python
# BEST — prune columns AND rows at read time (most efficient)
ds = Dataset.from_parquet("big.parquet", columns=["id", "text", "label"], filters=[("label", "==", 1)])
```

**Pattern 2: Parallelize across shards**
```python
# Each file processed in parallel
files = [f"shard-{i:05d}-of-00010.parquet" for i in range(10)]
ds = Dataset.from_parquet(files, num_proc=4, columns=["text"])
```

**Pattern 3: Fragment scan options for memory-constrained environments**
```python
import pyarrow.dataset as pds

opts = pds.ParquetFragmentScanOptions(
    use_buffered_stream=True,     # smaller reads
    buffer_size=8192,             # 8 KB read buffer
)
ds = Dataset.from_parquet("big.parquet", fragment_scan_options=opts)
```

**Pattern 4: Chaining from_parquet with dataset operations**
```python
ds = (
    Dataset
    .from_parquet("data.parquet", filters=[("lang", "==", "en")])
    .select_columns(["text", "label"])
    .shuffle(seed=42)
    .select(range(10000))
)
```

### 7. `ParquetConfig` Tuning

When using `load_dataset("parquet", ...)`, the `ParquetConfig` class controls behavior:

```python
from datasets import load_dataset
from datasets.packaged_modules.parquet.parquet import ParquetConfig

ds = load_dataset(
    "parquet",
    data_files="data.parquet",
    split="train",
    streaming=True,
    parquet_config=ParquetConfig(
        features=None,          # auto-detect
        schema=None,            # optional pyarrow schema
        batch_size=10000,       # rows per read batch (default: auto)
    )
)
```

### 8. Known Limitations

1. **Appending is not supported** — `from_parquet` creates a new Dataset; use `datasets.concatenate_datasets()` to merge
2. **Nested schema differences** — if Parquet files in a list have different schemas, loading may fail (use `features` to force schema)
3. **Predicate pushdown varies** — not all Parquet writers generate equally useful statistics for filter pruning
4. **Remote URLs** — `from_parquet()` does NOT accept HTTPS URLs directly (use `load_dataset("parquet", data_files="https://...")` with streaming instead)
5. **`fragment_scan_options` is PyArrow-specific** — only works with the PyArrow-backed reader

### Skill
mlops/hf-datasets-library — references/hf-learnings.md

---
## 2026-07-24: datasets-5.0.0-new-features — Agent Traces, Multi-Shard Shuffle, Batch-by-Column, New Formats (Topic #203, follow-on)

### Summary
Deep-dive into the specific new features shipped in `datasets` v5.0.0 (released 2026-06-05) — Agent traces parsing for SFT training, multi-input-shard streaming shuffle (breaking change), `batch(by_column=...)` for robotics episodes, and 4 new data format loaders (Apache Iceberg, TsFile IoT, 3D Mesh, CoNLL/CoNLL-U). This complements the earlier v5 overview (Topic #19) which covered Polars/SQL/Spark connectors.

### Source
GitHub Release v5.0.0 — https://github.com/huggingface/datasets/releases/tag/5.0.0
PyPI Latest: 5.0.0

---

## 1. Agent Traces — SFT-Ready Training Data from Agent Logs

**PR:** [#8232](https://github.com/huggingface/datasets/pull/8232) by @lhoestq
**Dependency:** `teich` library (new optional dep)

`datasets` can now load agent traces (Claude Code, Codex, Pi, etc.) and parse them into a `messages`-format column compatible with SFT training using `trl`.

### How it works

```python
from datasets import load_dataset

ds = load_dataset("lhoestq/agent-traces-example", split="train")
ds[0]["messages"]
# [{'role': 'user', 'content': 'Download a random dataset...'},
#  {'role': 'assistant', 'content': '...'},
#  ...]
```

The `teich` library extracts structured fields from raw trace logs:
- **`messages`** — chat-style conversation array (user ↔ assistant turns)
- **`prompt`** — the initial system/user prompt
- **`tools`** — tools/functions available to the agent
- **`metadata`** — timing, model info, token counts
- **`trace`** (renamed from `traces` — **minor breaking change**) — raw step-by-step trace

### Training on agent traces

```bash
trl sft --dataset-name lhoestq/agent-traces-example ...
```

### Discovery
All agent-traces datasets on the Hub can be found at:
https://huggingface.co/datasets?format=format:agent-traces&sort=trending

### Key insight
This bridges the gap between agent logging and supervised fine-tuning — you can collect real agent interaction logs, load them as datasets, and train better models from actual usage patterns.

---

## 2. Multi-Shard Shuffle Buffer — Breaking Change to `IterableDataset.shuffle()`

**PR:** [#8194](https://github.com/huggingface/datasets/pull/8194) by @lhoestq
**Issue:** [#8015](https://github.com/huggingface/datasets/issues/8015)

### The problem
The old `shuffle()` in streaming mode drew from a **single shard** — after exhausting the initial buffer (~1000 examples), every subsequent example came from the same shard, producing highly correlated (non-random) sequences.

### The fix
`shuffle()` now draws from **multiple input shards** simultaneously, producing genuinely random ordering throughout training.

```python
ds = load_dataset(..., streaming=True)
ds = ds.shuffle(seed=42)
# or configure manually:
ds = ds.shuffle(seed=42, buffer_size=1000, max_buffer_input_shards=10)
```

### Quantitative comparison (1024 shards × 123M items)

| Metric | Before (single shard) | After (multi-shard) |
|--------|----------------------|---------------------|
| Cold start diversity | All samples from same ~1 shard | Spread across ~10 shards |
| Nominal regime | Repeated IDs, correlated | Uniform distribution |
| Default `max_buffer_input_shards` | 1 (implicit) | **10** |

### Impact
- True random shuffle across the entire dataset for streaming mode
- Uses threads to fetch first examples from shards in parallel
- `state_dict()` / `load_state_dict()` still supported for checkpointing
- **Breaking change**: old behavior available via `max_buffer_input_shards=1`

---

## 3. `Dataset.batch(by_column=...)` — Grouped Batches

**PR:** [#8172](https://github.com/huggingface/datasets/pull/8172) by @lhoestq

Groups consecutive rows by a column value into a single batch — ideal for **robotics episodes**, **multi-turn conversations**, or any data where rows belong to groups that must not be split.

```python
from datasets import Dataset

ds = Dataset.from_dict({
    "episode": [0] * 10 + [1] * 10,
    "frame": list(range(10)) * 2,
})
ds = ds.batch(by_column="episode")
for x in ds:
    print(x)
# {'episode': [0, 0, ..., 0], 'frame': [0, 1, ..., 9]}
# {'episode': [1, 1, ..., 1], 'frame': [0, 1, ..., 9]}
```

### Implementation
- Uses PyArrow `ListArray` accumulation in an Arrow `map()` function
- Works with both `Dataset` (in-memory) and `IterableDataset` (streaming Parquet)
- Supports `state_dict()` / `load_state_dict()` for checkpointing
- **No multiprocessing** support (batch boundaries can span shards)

---

## 4. New Supported Data Formats

### 4a. Apache Iceberg (`iceberg`)

**PR:** [#8148](https://github.com/huggingface/datasets/pull/8148) by @frankliee

Support for loading Apache Iceberg tables directly via `pyiceberg`:

```python
from pyiceberg.catalog.sql import SqlCatalog
from datasets import load_dataset

catalog = SqlCatalog("my_catalog", uri="sqlite:///catalog.db", warehouse="/tmp/warehouse")
ds = load_dataset("iceberg", catalog=catalog, table_identifier="my_table")
```

Iceberg is the leading open table format for data lakes, supported by Databricks, Snowflake, AWS Glue, Dremio — removes friction of manual export-to-Parquet.

### 4b. TsFile (Apache IoTDB) — `tsfile`

**PR:** [#8160](https://github.com/huggingface/datasets/pull/8160) by @JackieTien97

Loads IoT time-series data from TsFile format with per-device wide format packaging:

```python
from datasets import load_dataset
ds = load_dataset("tsfile", data_files="sensor_data.tsfile")
```

### 4c. 3D Mesh — `Mesh` feature + `MeshFolder` builder

**PR:** [#8055](https://github.com/huggingface/datasets/pull/8055) by @Vinay-Umrethe

Adds `Mesh` as a first-class feature type (mirroring `Image`, `Audio`, `Video`):

```python
from datasets import load_dataset, Features, Mesh

features = Features({"mesh": Mesh()})
ds = load_dataset("mesh_folder", data_dir="path/to/meshes/", features=features)
```

- Self-contained binary formats: **GLB, PLY, STL**
- Uses PyArrow `struct` for raw bytes + file paths
- `MeshFolder` builder for directory-based loading
- Integrated into `WebDataset`, streaming, and push_to_hub

### 4d. CoNLL / CoNLL-U — `.conll` format loader

**PR:** [#8219](https://github.com/huggingface/datasets/pull/8219) by @CrypticCortex

Loads CoNLL-2003, CoNLL-2000, and Universal Dependencies formats directly:

```python
from datasets import load_dataset

ds = load_dataset(
    "conll",
    data_files="train.conll",
    column_names=["tokens", "pos_tags", "chunk_tags", "ner_tags"],
)
# Each example: {"tokens": [...], "pos_tags": [...], "chunk_tags": [...], "ner_tags": [...]}
```

One sentence per row, each column is a list aligned with the token list. Supports `.conll` and `.conllu` extensions.

---

## 5. Notable Bug Fixes & Improvements

| Fix | PR | Impact |
|-----|----|--------|
| Parquet streaming hangs at end of script | [#8176](https://github.com/huggingface/datasets/pull/8176) | Fixes infinite stall on last batch |
| Parquet `columns` arg fixed | [#8210](https://github.com/huggingface/datasets/pull/8210) | Column selection works correctly with Parquet |
| Parquet reshard fix | [#8193](https://github.com/huggingface/datasets/pull/8193) | Correct row group distribution after reshard |
| `fsspec` 2026.4.0 support | [#8175](https://github.com/huggingface/datasets/pull/8175) | Compatibility with latest filesystem spec |
| Composed splits in streaming | [#8220](https://github.com/huggingface/datasets/pull/8220) | `split="train+validation"` works in streaming mode |
| `num_proc` in `Dataset.to_sql` | [#7791](https://github.com/huggingface/datasets/pull/7791) | Parallel SQL writes |
| Map progress bar fix (`load_from_cache_file=False`) | [#8170](https://github.com/huggingface/datasets/pull/8170) | Bar no longer exceeds total |
| `None` preserved in `Json()` columns | [#8231](https://github.com/huggingface/datasets/pull/8231) | `None` stays `None`, not `"null"` string |
| Lance dataset streaming `storage_options` fix | [#8166](https://github.com/huggingface/datasets/pull/8166) | Correct credential passing for Lance |

---
## 2026-07-24: hf-datasets-500-agent-traces-json-type — v5.0.0 Agent Traces, Json() Type & Features (Topic #205)

### Summary
Datasets v5.0.0 (June 5, 2026) introduced major features for tool-calling/agent data: native **Agent traces** parsing via `teich`, the **Json() type** for arbitrary JSON in Arrow/Parquet, **multi-shard shuffling** in streaming mode (breaking change), **batch(by_column=...)** for episode-based grouping, storage buckets integration, and 4 new input formats (Iceberg, TsFile, 3D mesh, CoNLL).

### 1. Agent Traces — Native Agent Training Data Loading

The `teich` library (new optional dependency) parses agent traces from **claude_code**, **pi**, **codex**, and others into standard `messages` format for SFT training with `trl`:

```python
from datasets import load_dataset

# Auto-detected format:agent-traces — loads with teich parser
ds = load_dataset("lhoestq/agent-traces-example", split="train")
ds[0]["messages"]
# [{'role': 'user', 'content': 'Download a random dataset...'}, ...]

# Train directly
# trl sft --dataset-name lhoestq/agent-traces-example ...
```

**How it works:**
- `teich` library parses raw trace formats (JSONL with structured turn logs)
- Converts to `messages` column fitting OpenAI-style chat format
- Additional fields: `agent_trace_prompt`, `sent_at`, `count`
- Dataset repo format tag `format:agent-traces` enables auto-detection
- Discover all agent-traces datasets: https://huggingface.co/datasets?format=format:agent-traces&sort=trending

**Why it matters for Beer:** Beer's 8 tool-calling datasets can be tagged with `format:agent-traces` for discoverability and loaded directly into training pipelines without custom parsing.

### 2. Json() Type — Mixed-Type Fields in Arrow/Parquet

Tool-calling datasets often have fields mixing `str`, `int`, `float`, `dict`, `list` — normally rejected by Arrow's strict schema. The `Json()` type stores such data as JSON strings internally while presenting as native Python objects:

```python
from datasets import Features, Value, Json

features = Features({
    "messages": [{"role": Value("string"), "content": Json()}],
    "tool_calls": Json(),
})

ds = load_dataset("json", data_files="tool_data.jsonl", features=features)
ds[0]["tool_calls"]  # -> [{"name": "search", "args": {"q": "..."}}]
```

**Auto-detection** with `on_mixed_types="use_json"`:
```python
ds = Dataset.from_list(data, on_mixed_types="use_json")
# Mixed-type fields are auto-assigned Json() type
```

**Key properties:**
- Serialized as JSON string in Arrow, deserialized on access
- Supports `None` (preserved as `None`, not string `"null"`)
- Compatible with `.map()`, `.cast()`, `.from_dict()`, `.from_list()`
- Round-trips through Parquet with metadata preservation

### 3. Multi-Shard Shuffle — True Randomization in Streaming

**Breaking change in v5.0.0:** `IterableDataset.shuffle()` now pulls from multiple input shards simultaneously, solving the cold-start problem where only one shard's data appeared in the shuffle buffer:

```python
ds = load_dataset(..., streaming=True)
ds = ds.shuffle(seed=42)  # uses max_buffer_input_shards=10 by default

# Explicit configuration:
ds = ds.shuffle(seed=42, buffer_size=1000, max_buffer_input_shards=10)

# Old behavior (single shard):
ds = ds.shuffle(seed=42, max_buffer_input_shards=1)
```

**Before vs After:**
- Before: cold-start samples all came from shard 0 only (cluster of same shard)
- After: first 10 samples come from 10 different shards (truly distributed)
- Threads fetch first examples from input shards in parallel
- `state_dict()` / `load_state_dict()` checkpointing still works

### 4. batch(by_column=...) — Episode/Group Batching

For robotics, tool-use episodes, or any data grouped by a key:

```python
from datasets import Dataset

ds = Dataset.from_dict({
    "episode": [0] * 10 + [1] * 10,
    "frame": list(range(10)) * 2
})
batched = ds.batch(by_column="episode")
for x in batched:
    print(x)
# {'episode': [0, 0, ..., 0], 'frame': [0, 1, ..., 9]}
# {'episode': [1, 1, ..., 1], 'frame': [0, 1, ..., 9]}
```

Groups consecutive rows with same value in `by_column` into single batch rows. Works with both `Dataset` and `IterableDataset`.

### 5. Storage Buckets Integration (v4.8.0+)

Load raw data directly from Hugging Face Storage Buckets — no local intermediate:

```python
from datasets import load_dataset

# Load raw data from a Storage Bucket
ds = load_dataset("buckets/username/data-bucket", data_files=["*.jsonl"])

# Or using hf:// URIs
ds = load_dataset("json", data_files=["hf://buckets/username/data-bucket/*.jsonl"])

# Process and publish the AI-ready dataset
ds = ds.map(...).filter(...)
ds.push_to_hub("username/my-dataset-ready-for-training")
```

Also fixes multiprocessed `push_to_hub` on macOS (now uses `spawn` instead of `fork`).

### 6. New Supported Formats in v5.0.0

| Format | Builder | Use Case |
|--------|---------|----------|
| **Apache Iceberg** | `load_dataset("iceberg", ...)` | Large-scale tabular data with ACID transactions |
| **TsFile** (Apache IoTDB) | `load_dataset("tsfile", ...)` | Time-series IoT data, per-device wide format |
| **3D Mesh** | `load_dataset("mesh_folder", ...)` | 3D graphics, robotics simulation, CAD |
| **CoNLL** | `load_dataset("conll", ...)` / `conllu` | NER, POS tagging, parsing (CoNLL-2003/2000/U) |

### 7. Other Notable Fixes in v5.0.0

- **Parquet streaming hang fix** — no more infinite stall at end of script
- **Parquet `columns` arg fix** — column selection works correctly
- **Parquet reshard fix** — correct row group distribution
- **Composed splits in streaming** — `split="train+validation"` now works
- **`None` in Json() columns** — stays `None`, not `"null"` string
- **Map progress bar fix** — `load_from_cache_file=False` no longer exceeds total
- **Lance streaming `storage_options`** — correct credential passing

### Source
- Official v5.0.0 release: https://github.com/huggingface/datasets/releases/tag/5.0.0
- Agent traces PR: https://github.com/huggingface/datasets/pull/8232
- Multi-shard shuffle PR: https://github.com/huggingface/datasets/pull/8194
- batch(by_column) PR: https://github.com/huggingface/datasets/pull/8172
- Iceberg support PR: https://github.com/huggingface/datasets/pull/8148
- 3D Mesh PR: https://github.com/huggingface/datasets/pull/8055
- CoNLL format PR: https://github.com/huggingface/datasets/pull/8219
- Storage buckets: https://huggingface.co/docs/datasets/en/loading#storage-buckets
- Json() type PR: https://github.com/huggingface/datasets/pull/8027

---

### Skill
mlops/hf-datasets-library — references/hf-learnings.md

### References
- https://github.com/huggingface/datasets/releases/tag/5.0.0
- https://huggingface.co/docs/datasets/en/parquet_processing
- https://huggingface.co/docs/datasets/v5.0.0/en/package_reference/main_classes#datasets.Dataset.from_parquet
- https://arrow.apache.org/docs/python/dataset.html#filtering-data
- https://huggingface.co/docs/datasets/en/stream
- https://huggingface.co/docs/datasets-server/parquet
- https://github.com/huggingface/datasets/pull/8232 — Agent traces PR
- https://github.com/huggingface/datasets/pull/8194 — Multi-shard shuffle PR
- https://github.com/huggingface/datasets/pull/8172 — batch(by_column) PR
- https://github.com/huggingface/datasets/pull/8148 — Iceberg support PR
- https://github.com/huggingface/datasets/pull/8055 — 3D Mesh PR
- https://github.com/huggingface/datasets/pull/8219 — CoNLL format PR

---

## 2026-07-24: hf-datasets-pytorch-integration-deep-dive

### Summary
Deep-dive into how Hugging Face `datasets` integrates with PyTorch — covering `with_format("torch")`, `set_transform()`, zero-copy Arrow→tensor conversion, PyTorch DataLoader integration, multi-worker loading, streaming with workers, distributed splitting, N-dimensional array handling, and the `StatefulDataLoader` checkpointing pattern.

### Key API Surface

#### `with_format("torch")` — Format the Dataset for PyTorch

```python
from datasets import Dataset
ds = Dataset.from_dict({"data": [[1, 2], [3, 4], [5, 6]]})

# Set format to PyTorch (zero-copy from Arrow)
ds = ds.with_format("torch")
ds[0]  # {'data': tensor([1, 2])}
ds[:2] # {'data': tensor([[1, 2], [3, 4]])}
```

**GPU device support:**
```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ds = ds.with_format("torch", device=device)  # loads tensors directly on GPU
```

**Column filtering with format:**
```python
# Only return specific columns as tensors
ds = ds.with_format("torch", columns=["input_ids", "attention_mask"])
```

**`output_all_columns` — mix of tensor and non-tensor columns:**
```python
ds = ds.with_format("torch", columns=["data"], output_all_columns=True)
# Returns {'data': tensor([1, 2]), 'label': 0} — label stays as Python int
```

**`formatted_as()` — temporary format without mutating the dataset:**
```python
with ds.formatted_as("torch", device="cuda"):
    batch = ds[0]  # tensors on GPU
# outside the context, original format is restored
```

#### N-Dimensional Array Handling

**Fixed shape → single tensor (efficient):**
```python
from datasets import Dataset, Features, Array2D

data = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
features = Features({"data": Array2D(shape=(2, 2), dtype='int32')})
ds = Dataset.from_dict({"data": data}, features=features)
ds = ds.with_format("torch")
ds[:2]["data"].shape  # torch.Size([2, 2, 2]) — single tensor
```

**Variable shape → list of tensors (slower):**
```python
data = [[[1, 2], [3]], [[4, 5, 6], [7, 8]]]  # varying shapes
ds = Dataset.from_dict({"data": data})
ds = ds.with_format("torch")
ds[0]  # {'data': [tensor([1, 2]), tensor([3])]}
```

**Critical performance rule:** Always explicitly declare `Array2D`, `Array3D`, `Array4D`, or `Array5D` features with fixed shapes. The library falls back to slow shape comparison logic when shapes aren't declared.

#### Image Feature Type → Tensor

```python
from datasets import Features, Image

features = Features({"image": Image()})
ds = Dataset.from_dict({"image": ["path/to/img.png"]}, features=features)
ds = ds.with_format("torch")
ds[0]["image"].shape  # torch.Size([512, 512, 4]) — HWC, uint8
ds[:2]["image"].shape # torch.Size([2, 512, 512, 4])
```

#### Audio Feature Type → Tensor

```python
from datasets import Features, Audio

features = Features({"audio": Audio()})
ds = Dataset.from_dict({"audio": ["path/to/audio.wav"]}, features=features)
ds = ds.with_format("torch")
ds[0]["audio"]["array"]          # tensor of waveform samples
ds[0]["audio"]["sampling_rate"]  # tensor(44100)
```

#### ClassLabel → Tensor

```python
from datasets import Features, ClassLabel

features = Features({"label": ClassLabel(names=["neg", "pos"])})
ds = Dataset.from_dict({"label": [0, 0, 1]}, features=features)
ds = ds.with_format("torch")
ds[:3]  # {'label': tensor([0, 0, 1])}
```

**String/binaries are unchanged** — PyTorch only supports numeric types.

#### `set_transform()` — On-the-Fly Transforms (No Cache File)

```python
def encode(batch):
    """Applied per-batch during DataLoader iteration — no cache files written."""
    return tokenizer(batch["text"], padding="longest", truncation=True, return_tensors="pt")

# with_transform returns a context that applies `encode` on every __getitem__ call
ds = ds.with_transform(encode)

# Against: returns tokenizer output directly
ds[0]  # {'input_ids': tensor([...]), 'attention_mask': tensor([...])}
```

**Key traits:**
- No cache file is written — transform runs fresh every access
- Use `with_transform()` for tokenization inside a DataLoader to avoid storing pre-tokenized data
- Combine with `with_format("torch")` for base tensor conversion + custom transform for specialized output

#### `set_format()` vs `with_transform()` — The Difference

| Method | Cached? | Purpose |
|--------|---------|---------|
| `with_format("torch")` | No (zero-copy) | Converts Arrow arrays to PyTorch tensors on-the-fly |
| `with_transform(fn)` | No | Passes rows through a user-defined callable on every access |
| `map(fn)` | Yes (to Arrow cache) | Persists processed data to disk as Arrow tables |

Use `with_format()` for fast tensor access. Use `with_transform()` for tokenization inside DataLoaders. Use `map()` when you need to precompute and persist results.

### PyTorch DataLoader Integration

A `Dataset` object (map-style) can be passed directly to `torch.utils.data.DataLoader`:

```python
import numpy as np
from datasets import Dataset
from torch.utils.data import DataLoader

ds = Dataset.from_dict({
    "data": np.random.rand(16),
    "label": np.random.randint(0, 2, size=16)
}).with_format("torch")

dataloader = DataLoader(ds, batch_size=4)
for batch in dataloader:
    print(batch)
    # {'data': tensor([...]), 'label': tensor([...])}
```

**With custom collation (e.g., `DataCollatorForLanguageModeling`):**

```python
from transformers import DataCollatorForLanguageModeling
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
collator = DataCollatorForLanguageModeling(tokenizer)

ds = load_dataset("wikitext", "wikitext-2-raw-v1", split="train", streaming=True)
ds = ds.map(lambda x: tokenizer(x["text"]), batched=True)
dataloader = DataLoader(ds, batch_size=8, collate_fn=collator)
```

**`IterableDataset` (streaming) with DataLoader:**

```python
ds = load_dataset("bigcode/the-stack", split="train", streaming=True)
dataloader = DataLoader(ds, batch_size=32)  # works directly
# IterableDataset inherits from torch.utils.data.IterableDataset
```

### Multi-Worker Data Loading

#### Map-Style Dataset with Workers

```python
# Save to disk for worker-safe reloading
from datasets import load_from_disk

ds.save_to_disk("my_dataset")
ds = load_from_disk("my_dataset").with_format("torch")

dataloader = DataLoader(ds, batch_size=32, num_workers=4)
```

**How it works:**
- Each worker process reloads the dataset from the Arrow-mapped files
- Arrow memory-mapped files are **shared** across processes (OS-level shared memory)
- Workers don't duplicate the data in RAM — they re-map the same files
- Each worker gets a subset of the dataset's shards

#### Streaming (IterableDataset) with Workers

```python
ds = load_dataset("deepmind/code_contests", streaming=True, split="train")
print(ds.num_shards)  # 39
dataloader = DataLoader(ds, batch_size=32, num_workers=4)
```

**How it works:**
- Each worker is assigned a **subset of shards** to stream from
- `num_workers` can't exceed `num_shards` — each worker needs at least one shard
- Workers stream independently from remote or local storage

#### Sharding with `to_iterable_dataset()` for Fine-Grained Control

```python
# Convert a map-style dataset to sharded iterable
ds = load_dataset("ethz/food101")
iterable_ds = ds.to_iterable_dataset(num_shards=64)
iterable_ds = iterable_ds.shuffle(buffer_size=10_000)

# 64 shards ÷ 4 workers = 16 shards per worker
dataloader = DataLoader(iterable_ds, num_workers=4)
```

### Distributed Training Support

#### `split_dataset_by_node()`

```python
import os
from datasets.distributed import split_dataset_by_node

rank = int(os.environ["RANK"])
world_size = int(os.environ["WORLD_SIZE"])

# Works for both Dataset and IterableDataset
ds = split_dataset_by_node(ds, rank=rank, world_size=world_size)
```

**For map-style Dataset:**
- Each node gets a contiguous chunk of data (rank 0 = first chunk)
- Contiguous chunks maximize throughput (sequential disk reads)

**For IterableDataset:**
- If `num_shards % world_size == 0`, shards are evenly assigned across nodes (optimal)
- Otherwise, each node keeps 1 example out of `world_size`, skipping others
- ⚠️ If shuffling in distributed mode, set a **fixed seed** in `IterableDataset.shuffle(seed=...)` so all nodes use the same shuffled shard list

#### Combine with DataLoader and Workers

```python
# Each node gets its split, then uses 4 workers each
ds = split_dataset_by_node(ds, rank=rank, world_size=world_size)
dl = DataLoader(ds, batch_size=32, num_workers=4)
```

### Checkpoint DataLoader State (Resume Training)

```python
from torchdata.stateful_dataloader import StatefulDataLoader

ds = load_dataset("deepmind/code_contests", streaming=True, split="train")
dataloader = StatefulDataLoader(ds, batch_size=32, num_workers=4)

# Save checkpoint mid-epoch
state_dict = dataloader.state_dict()
torch.save(state_dict, "dataloader_state.pt")

# Resume from checkpoint
dataloader.load_state_dict(torch.load("dataloader_state.pt"))
```

This works because `IterableDataset` implements `state_dict()` and `load_state_dict()`.

### Shuffling in Streaming Mode

```python
# Buffer-based approximate shuffling
shuffled = ds.shuffle(seed=42, buffer_size=10_000)
```

**How buffer shuffling works:**
1. Fill a buffer with the first `buffer_size` examples
2. Randomly sample from the buffer (with replacement)
3. Replace sampled examples with new ones from the stream
4. Larger buffer = better shuffle quality, more memory
5. Default buffer size = 1,000

**Epoch reshuffling:**
```python
for epoch in range(epochs):
    shuffled_dataset.set_epoch(epoch)  # seed = initial_seed + epoch
    for example in shuffled_dataset:
        ...
```

### batching via `.batch()` Method

```python
# Direct batching without DataLoader (streaming)
batched = ds.batch(batch_size=32)
batched = ds.batch(batch_size=32, drop_last_batch=True)

for batch in batched:
    print(batch)  # list of dicts
```

### Training Loop Example

```python
import torch
from torch.utils.data import DataLoader
from transformers import AutoModelForMaskedLM, DataCollatorForLanguageModeling
from datasets import load_dataset

# Streaming dataset
dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="train", streaming=True)
dataset = dataset.shuffle(seed=42, buffer_size=10_000)
dataset = dataset.with_format("torch")

# DataLoader with collator
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
collator = DataCollatorForLanguageModeling(tokenizer)
dataloader = DataLoader(dataset, batch_size=8, collate_fn=collator)

# Training
model = AutoModelForMaskedLM.from_pretrained("distilbert-base-uncased")
model.train().to("cuda")

for batch in dataloader:
    batch = {k: v.to("cuda") for k, v in batch.items()}
    outputs = model(**batch)
    loss = outputs.loss
    loss.backward()
    optimizer.step()
```

### Key Insights

1. **Zero-copy is the killer feature** — Arrow→PyTorch tensor conversion via `with_format("torch")` is nearly free (just metadata). No serialization or memcpy.

2. **Pre-define array shapes** for N-dimensional data. Without explicit `Array2D`/`Array3D` features, the library does expensive shape comparison and falls back to list-of-tensors.

3. **`with_transform()` for tokenization** inside a DataLoader — avoids writing pre-tokenized data to cache, saving disk space and time.

4. **`map()` caches by default** — fingerprint-based caching means re-running the same map loads from cache. Use `load_from_cache_file=False` for non-deterministic transforms.

5. **Worker-based loading with map-style datasets** requires `save_to_disk()` first — the Arrow files must exist on disk for workers to memory-map them.

6. **Streaming `num_workers` is shard-limited** — you can't have more workers than shards. Use `to_iterable_dataset(num_shards=N)` to increase shard count.

7. **Distributed splitting** with `split_dataset_by_node()` works for both map and iterable datasets, but iterable shard-count-based splitting is more efficient when `num_shards % world_size == 0`.

8. **`StatefulDataLoader`** from `torchdata` enables mid-epoch checkpoint/resume — essential for long training runs on preemptible infrastructure.

9. **String/binary columns are silently ignored** by `with_format("torch")` — they stay as Python objects.

10. **`formatted_as()` context manager** is the safest way to use temporary tensor formats without mutating the dataset.

### Sources
- https://huggingface.co/docs/datasets/en/use_with_pytorch — official guide
- https://huggingface.co/docs/datasets/en/stream — streaming guide
- https://huggingface.co/docs/datasets/en/process — process guide
- https://huggingface.co/docs/datasets/en/package_reference/main_classes — Dataset API reference
- Source: `src/datasets/formatting/formatting.py` — formatting internals
- Source: `src/datasets/distributed.py` — `split_dataset_by_node`
- https://pytorch.org/docs/stable/data.html — PyTorch DataLoader docs
- https://github.com/pytorch/data — StatefulDataLoader
