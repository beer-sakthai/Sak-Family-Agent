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

## 2026-07-24: hf-datasets-streaming-iterable-dataset — Streaming & IterableDataset Deep Dive

### Summary
`IterableDataset` is the streaming variant of `Dataset`. It doesn't load data into memory — it yields examples one at a time from the source. Supports `.map()`, `.filter()`, `.shuffle()`, `.take()`, `.skip()`, and `.batch()`. Key limitation: no random access (`ds[42]`), no `len()` for multi-shard sets.

### Key Methods
| Method | Description |
|--------|-------------|
| `.take(n)` | Get first n examples |
| `.skip(n)` | Skip first n examples |
| `.shuffle(buffer_size, seed)` | Approximate shuffle with buffer |
| `.batch(batch_size)` | Group into fixed-size batches |
| `.map(fn)` | Transform each example |
| `.filter(fn)` | Keep examples matching predicate |
| `.repeat(num)` | Repeat the stream n times |
| `.reshard(num_shards)` | Redistribute shards across workers |

### When to Use
- Dataset larger than available RAM
- Remote data on the Hub
- Training loops that only need one pass at a time
- When you want to avoid disk usage

### Key Limitations
1. **No `len()`** for multi-shard streaming datasets (unknown total until full iteration)
2. **No random access** — cannot index like `ds[42]`
3. **Shuffle is approximate** — buffer-based, not global Fisher-Yates
4. **Single-process `.map()`** — no `num_proc` for parallel processing
5. **Shuffle buffer lost on checkpoint resume** — buffer is drained and refilled
6. **Network-dependent** — iterating requires network access to the Hub

### Source
- Official docs: https://huggingface.co/docs/datasets/en/stream
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
