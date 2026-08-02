# HF Learnings — HuggingFace Datasets Arrow Memory Architecture

## 2026-07-25: hf-datasets-arrow-memory-architecture — Deep Dive (Topic #370)

### Summary

Comprehensive source-code level deep dive into how HuggingFace Datasets manages memory through Apache Arrow. The library implements a **dual-model table architecture** — `InMemoryTable` (loads data into RAM) and `MemoryMappedTable` (maps from disk with lazy replay), joined via `ConcatenationTable` as a block container. The decision between them is controlled by `IN_MEMORY_MAX_SIZE` (default 0 = always memory-mapped). Arrow itself uses **mimalloc** as its default memory pool in PyArrow 25+. Streaming mode bypasses this entirely, using iterators over shards with configurable retry logic.

Key insight: Datasets' memory model is not "one approach" but a **layered composition** — blocks of different table types coexist in a single `ConcatenationTable`, each block independently deciding whether to hold data in RAM or map from disk. The "replay" system in `MemoryMappedTable` provides zero-copy deserialisation at the cost of re-executing transforms on load.

---

### 1. The Table Hierarchy

```
IndexedTableMixin (mixin: fast_slice, fast_gather)
  └── Table (base: wraps pyarrow.Table + nbytes/column_names)
        ├── TableBlock (abstract: slice, filter, flatten, cast, combine_chunks)
        │     ├── InMemoryTable      — data lives in RAM
        │     └── MemoryMappedTable  — data mapped from disk, replays
        └── ConcatenationTable       — block container (mix of both)
```

**`Table`** (line 210): Base class wrapping a `pa.Table`. Provides column access, `nbytes`, `num_rows`, and delegates to pyarrow for operations.

**`TableBlock`** (line 685): Abstract subclass representing a single contiguous block of data. Defines the interface: `slice`, `filter`, `flatten`, `cast`, `combine_chunks`. All return new `TableBlock` instances.

**`InMemoryTable`** (line 695): Loads **all data into RAM** via `pa.ipc.open_stream()`. Pickling copies all data in memory. Best for datasets that fit comfortably in available RAM.

**`MemoryMappedTable`** (line 1046): Uses `pa.memory_map()` to read data from disk on demand. Pickling stores **only the path + replay list** — deserialised by re-mapping and replaying transforms. Implements a **replay pattern** for zero-copy deserialisation.

**`ConcatenationTable`** (line 1330): A collection of "blocks" (each block is a `list[TableBlock]`). Blocks can be different types — some `InMemoryTable`, some `MemoryMappedTable`. Supports concatenation on axis 0 (append rows) and axis 1 (append columns). Missing columns are filled with null via `pa.concat_tables(promote=True)`.

```python
# Example: Mixed blocks in a ConcatenationTable
from datasets.table import InMemoryTable, MemoryMappedTable, ConcatenationTable

block_a = InMemoryTable(pa.table({"x": [1, 2]}))
block_b = MemoryMappedTable.from_file("data.arrow")

combined = ConcatenationTable.from_blocks([[block_a, block_b]])
# combined.blocks = [[InMemoryTable(...), MemoryMappedTable(...)]]
```

---

### 2. Memory-Mapped Architecture (Deep Dive)

#### 2.1 The Replay System

`MemoryMappedTable` stores a **replay log** — an ordered list of `(method_name, args, kwargs)` tuples representing every transform applied since the table was loaded from disk. When the table is pickled for serialisation, only the file path and replay list are saved. On `__setstate__`, the table is re-mapped from disk and all replays are re-applied.

```python
# MemoryMappedTable.__getstate__ (line 1078)
def __getstate__(self):
    return {"path": self.path, "replays": self.replays}

# MemoryMappedTable.__setstate__ (line 1081)
def __setstate__(self, state):
    path = state["path"]
    replays = state["replays"]
    table = _memory_mapped_arrow_table_from_file(path)  # re-maps from disk
    table = self._apply_replays(table, replays)          # re-applies transforms
    MemoryMappedTable.__init__(self, table, path=path, replays=replays)
```

Supported replay operations:
- `slice(offset, length)` — row range selection
- `filter(mask, ...)` — boolean mask filtering
- `flatten(...)` — struct column flattening
- `cast(schema, ...)` — schema cast
- `combine_chunks(...)` — chunk consolidation
- Any other `pa.Table` method via generic `getattr(table, name)(*args, **kwargs)`

**Trade-off**: Zero-copy deserialisation + memory efficiency vs. re-execution cost on every unpickle.

#### 2.2 File Reading Strategies

| Strategy | Function | Method | Memory |
|----------|----------|--------|--------|
| In-memory | `_in_memory_arrow_table_from_file` (line 33) | `pa.input_stream()` + `pa.ipc.open_stream().read_all()` | All data loaded |
| Memory-mapped | `_memory_mapped_record_batch_reader_from_file` (line 47) | `pa.memory_map()` + `pa.ipc.open_stream()` | On-demand from disk |
| Schema only | `read_schema_from_file` (line 52) | `pa.memory_map()` + schema only | Minimal |

#### 2.3 Zero-Copy Slicing

`MemoryMappedTable.slice()` (line 1105) uses **zero-copy slicing** via Arrow's `Table.slice()` — no data is copied, only view metadata changes. The replay simply records the offset and length.

```python
def slice(self, offset=0, length=None):
    replay = ("slice", (offset, length), {})
    replays = self._append_replay(replay)
    return MemoryMappedTable(self.fast_slice(offset=offset, length=length), self.path, replays)
```

---

### 3. ConcatenationTable Block Composition

`ConcatenationTable` stores a **2D block grid**: `blocks: list[list[TableBlock]]`. The outer list concatenates on axis 0 (rows), the inner list concatenates on axis 1 (columns).

```python
# blocks[0] = [table_x, table_y]  → horizontal concat (axis=1)
# blocks[1] = [table_z]           → vertical concat (axis=0) of previous result
```

**Block consolidation** (line 1427): When blocks are merged, adjacent blocks of the same type are consolidated:
- `InMemoryTable` + `InMemoryTable` → merged into one `InMemoryTable` via `pa.concat_tables()`
- `MemoryMappedTable` + `MemoryMappedTable` stay separate (each has its own path)

**`_split_both_like`** (line 1476): When concatenating on axis 1 (columns), both block sets must have the same row boundaries. This method splits blocks at matching row boundaries so columns align correctly.

```python
# Example: Splitting to align rows
# Result has 2 row_blocks of 3 rows each
# Blocks have 3 row_blocks of 2 rows each
# → Both get split into 4 row_blocks of sizes [2, 1, 1, 2]
```

---

### 4. Memory Decision Logic

When loading a dataset, the library decides between `InMemoryTable` and `MemoryMappedTable` based on dataset size:

```python
# arrow_dataset.py line 2073
keep_in_memory = keep_in_memory if keep_in_memory is not None else is_small_dataset(dataset_size)
table_cls = InMemoryTable if keep_in_memory else MemoryMappedTable
```

**`is_small_dataset()`** (info_utils.py):
```python
def is_small_dataset(dataset_size):
    if dataset_size and config.IN_MEMORY_MAX_SIZE:
        return dataset_size < config.IN_MEMORY_MAX_SIZE
    else:
        return False
```

**`estimate_dataset_size()`** (file_utils.py):
```python
def estimate_dataset_size(paths):
    return sum(path.stat().st_size for path in paths)
```

Key environment variables:

| Variable | Default | Effect |
|----------|---------|--------|
| `HF_DATASETS_IN_MEMORY_MAX_SIZE` | `0` (disabled) | If set > 0, datasets smaller than this (bytes) use `InMemoryTable` |
| `HF_DATASETS_CACHE` | `~/.cache/huggingface/datasets` | Cache directory for downloaded and processed datasets |
| `HF_DATASETS_OFFLINE` | unset | Disables all network access |

With `IN_MEMORY_MAX_SIZE=0` (default), **all** loaded datasets use `MemoryMappedTable` — data is never fully loaded into RAM unless explicitly accessed.

---

### 5. Arrow Memory Pools

PyArrow 25.0.0 (bundled with Datasets 5) uses **mimalloc** as the default memory allocator:

```python
>>> pa.default_memory_pool()
<pyarrow.MemoryPool backend_name=mimalloc bytes_allocated=0 max_memory=128>
```

The `max_memory=128` indicates PyArrow tracks up to 128 bytes of internal accounting (not a hard limit). Actual memory allocation is delegated to mimalloc, which provides:
- Fast allocation/deallocation
- Minimal fragmentation
- Thread-local caching

**`MAX_TABLE_NBYTES_FOR_PICKLING`** (config.py:274): Set to `4 << 30` (4 GiB). Tables larger than this use a different pickling path.

---

### 6. Batch Sizing Architecture

#### 6.1 Arrow Record Batch Sizes

Controlled by `config.py` constants that adapt to data modality:

| Constant | Default | Used Where |
|----------|---------|-----------|
| `ARROW_READER_BATCH_SIZE_IN_DATASET_ITER` | 10 | `Dataset.__iter__()` preloaded rows |
| `DEFAULT_MAX_BATCH_SIZE` | 1000 | General batch operations |
| `ARROW_RECORD_BATCH_SIZE_FOR_AUDIO_DATASETS` | 100 | Audio datasets |
| `ARROW_RECORD_BATCH_SIZE_FOR_IMAGE_DATASETS` | 100 | Image datasets |
| `ARROW_RECORD_BATCH_SIZE_FOR_BINARY_DATASETS` | 100 | Binary datasets |
| `ARROW_RECORD_BATCH_SIZE_FOR_VIDEO_DATASETS` | 10 | Video datasets (larger per-row size) |

The `get_arrow_writer_batch_size_from_features()` function (arrow_writer.py:66) computes the minimum batch size by inspecting all feature types, ensuring multi-modal datasets use conservative batch sizes appropriate for the largest modality.

#### 6.2 Parquet Row Group Sizes

| Constant | Default |
|----------|---------|
| `MAX_ROW_GROUP_SIZE` | `"100MB"` |
| `MAX_SHARD_SIZE` | `"500MB"` |
| `PARQUET_ROW_GROUP_SIZE_FOR_AUDIO_DATASETS` | `None` (uses MAX_ROW_GROUP_SIZE) |
| `PARQUET_ROW_GROUP_SIZE_FOR_IMAGE_DATASETS` | `None` |
| `PARQUET_ROW_GROUP_SIZE_FOR_BINARY_DATASETS` | `None` |
| `PARQUET_ROW_GROUP_SIZE_FOR_VIDEO_DATASETS` | `None` |

`get_writer_batch_size_from_data_size()` (arrow_writer.py:145) adjusts batch size based on actual data byte size, capping row groups to under 2 GiB to avoid Arrow overflow.

#### 6.3 Writer Overflow Protection

Arrow has a 2 GiB batch size limit. The writer catches overflow errors and suggests reducing `writer_batch_size`:
```python
# arrow_writer.py line 388
except pa.ArrowException as e:
    if "overflow" in str(e).lower() or "large" in str(e).lower():
        raise OverflowError(
            f"There was an overflow with type {type_(data)}. "
            "Try to reduce writer_batch_size to have batches smaller than 2GB.\n({e})"
        )
```

---

### 7. Formatting Layer and Memory

When data is accessed with `set_format()`, the formatting layer converts Arrow data to Python/numpy/torch/pandas. This **can create memory copies** depending on format:

| Format | Data Path | Zero-Copy? |
|--------|-----------|-----------|
| **Arrow** (default) | `SimpleArrowExtractor` — returns raw `pa.Table` | ✅ Yes |
| **Python** | `PythonArrowExtractor` — `pa_table.to_pydict()` | ❌ No (creates Python objects) |
| **NumPy** | `NumpyArrowExtractor` — `pa_array.to_numpy(zero_copy_only=...)` | ⚠️ Partial |
| **Pandas** | `PandasArrowExtractor` — `pa_table.to_pandas()` | ❌ No |
| **Torch** | `TorchArrowExtractor` via `torch.from_numpy()` | ❌ No (depends on NumPy) |
| **Polars** | `PolarsArrowExtractor` — wraps existing Arrow data | ✅ Yes (zero-copy) |

**NumPy zero-copy conditions** (formatting.py:166-202):
- Only possible when `_is_zero_copy_only()` returns True for the dtype
- Fails when nulls are present (null bitmask requires expansion)
- For `ArrayXD` extension types, checks the storage dtype

**Practical implication**: Reading a 10 GB dataset as Python/dict iterates through `to_pydict()` which materialises everything in RAM. Reading as Arrow (default) streams from memory-mapped file.

---

### 8. Streaming Mode Memory Management

Streaming mode (`load_dataset(..., streaming=True)`) completely bypasses the table hierarchy. Instead of `Dataset` with `ConcatenationTable`, it creates an `IterableDataset` that:

1. **Opens HTTP/fs connections** to shard files (retry logic: 20 retries, 5s intervals)
2. **Reads one record batch at a time** from the streaming reader
3. **Applies transforms on-the-fly** (map/filter/shuffle applied lazily)
4. **Never materialises the full dataset** in memory

Streaming shuffle uses a **buffer** (default 1000 examples) that is drawn from **multiple shards** simultaneously in Datasets 5 (`max_buffer_input_shards=10`).

```python
# Streaming shuffle buffer (iterable_dataset.py)
ds = load_dataset("big-data", streaming=True)
ds = ds.shuffle(seed=42, buffer_size=1000, max_buffer_input_shards=10)
# Buffer stays at ~1000 examples; no full-dataset materialisation
```

**Converting map-style to iterable** (arrow_dataset.py:5738):
```python
ds = load_dataset("big-data", split="train")  # map-style (MemoryMappedTable)
it_ds = ds.to_iterable_dataset(num_shards=4)  # streaming from local files
# Much faster than re-downloading since data is already cached locally
```

---

### 9. Cache File Structure

Dataset cache on disk:

```
$HF_DATASETS_CACHE/
└── <dataset_name>/
    └── <config>/
        └── <version>/
            └── <hash>/
                ├── dataset.arrow       # Main data (Arrow IPC format)
                ├── indices.arrow       # Optional index mapping (shuffle/select)
                ├── state.json          # Dataset state (format, fingerprint)
                └── dataset_info.json   # Features, splits, metadata
```

- **`dataset.arrow`**: Written by `ArrowWriter` in record batch format. Memory-mapped on load.
- **`indices.arrow`**: Created when `shuffle()`, `select()`, or `train_test_split()` is applied. Maps logical row → physical row.
- **`state.json`**: Serialised dataset configuration including format settings, fingerprint, and split info.

---

### 10. Best Practices

#### 10.1 When to Force In-Memory

```python
import datasets
import os

# Force in-memory for datasets < 2 GB
os.environ["HF_DATASETS_IN_MEMORY_MAX_SIZE"] = str(2 * 1024**3)
# Or explicitly per load:
ds = load_dataset("my-dataset", keep_in_memory=True)
```

Use when:
- Dataset fits comfortably in RAM
- Random access latency must be minimal (memory-mapped has page-fault overhead)
- Dataset is accessed repeatedly in a single session

#### 10.2 When to Use Memory-Mapped (Default)

Use when:
- Dataset exceeds available RAM
- Only subset of data needed per training step
- Multiple processes share the same dataset (OS page cache shared)
- Working with images/audio/video (large external files)

#### 10.3 When to Use Streaming

```python
ds = load_dataset("massive-dataset", streaming=True)
```

Use when:
- Dataset far exceeds available RAM
- Only one sequential pass needed (e.g., training epoch)
- Disk space is limited (streaming doesn't cache full dataset)
- Dataset is sharded across many files (parallel shard reading)

#### 10.4 Memory-Efficient Iteration

```python
# BAD: Creates full Python dict in memory
for row in ds:
    process(row["text"])

# GOOD: Uses Arrow batches, minimises Python overhead
for batch in ds.iter(batch_size=100):
    process(batch["text"])  # batch["text"] is Arrow ChunkedArray

# BEST: Use Arrow format for zero-copy
ds_arrow = ds.with_format("arrow")
for batch in ds_arrow.iter(batch_size=100):
    # batch is a pyarrow.Table slice — zero copy from memory-mapped file
    process(batch)
```

#### 10.5 Memory-Efficient Format Selection

```python
# For training loops — use the native format of your framework
# Pytorch
ds = ds.with_format("torch")  # Converts on access

# For data analysis — use Arrow format to avoid copies
ds = ds.with_format("arrow")

# For maximum memory efficiency with complex types
ds = ds.with_format("numpy", zero_copy_only=True)
```

#### 10.6 Sharding for Memory Control

```python
# Manually shard to control per-process memory
ds = load_dataset("big-data", split="train")
shards = ds.shard(num_shards=10, index=0)

# Or use iterable shards for streaming
it_ds = ds.to_iterable_dataset(num_shards=10)
```

---

### 11. Key Environment Variables Summary

| Variable | Default | Effect |
|----------|---------|--------|
| `HF_DATASETS_IN_MEMORY_MAX_SIZE` | `0` | Bytes threshold for in-memory vs memory-mapped |
| `HF_DATASETS_CACHE` | `~/.cache/huggingface/datasets` | Cache location |
| `HF_DATASETS_OFFLINE` | unset | Disable network |
| `HF_DATASETS_DISABLE_PROGRESS_BARS` | unset | Disable tqdm |
| `HF_DATASETS_MULTITHREADING_MAX_WORKERS` | `16` | Parallelism limit |

---

### 12. Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    Dataset (map-style)                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │              ConcatenationTable                     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │Block 1   │  │Block 2   │  │Block 3   │          │  │
│  │  │InMemory  │  │MemMapped │  │MemMapped │          │  │
│  │  │RAM       │  │File A    │  │File B    │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  indices.arrow  (optional: shuffle/select mapping)  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Format Layer  (arrow | python | numpy | torch)    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│              IterableDataset (streaming)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │Shard 1   │  │Shard 2   │  │Shard 3   │               │
│  │HTTP/fs   │  │HTTP/fs   │  │HTTP/fs   │               │
│  └──────────┘  └──────────┘  └──────────┘               │
│       │              │             │                     │
│       └──────────────┼─────────────┘                     │
│                      ▼                                   │
│             ┌────────────────┐                           │
│             │ Shuffle Buffer  │  (max_buffer_input=10)   │
│             │ (1000 entries)  │                           │
│             └────────────────┘                           │
│                      │                                   │
│                      ▼                                   │
│             map → filter → transform chain               │
└──────────────────────────────────────────────────────────┘
```

---

### 13. Skill Created

`hf-datasets-arrow-memory-architecture/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with complete documentation.

### Sources

- `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/table.py` — Table class hierarchy (lines 1-2482)
- `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/arrow_dataset.py` — Dataset class, formatting integration
- `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/arrow_writer.py` — ArrowWriter, batch size computation
- `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/config.py` — All memory/batch/streaming configuration
- `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/formatting/formatting.py` — Format extractors (zero-copy analysis)
- `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/utils/info_utils.py` — `is_small_dataset` function
- `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/utils/file_utils.py` — `estimate_dataset_size` function
- https://huggingface.co/docs/datasets/main/en/ — Official Datasets documentation
- https://arrow.apache.org/docs/python/memory.html — PyArrow memory management docs
