# HF Datasets from_parquet — Deep Dive

**Learned:** 2026-07-25 | **Topic:** `hf-datasets-from-parquet`
**Sources:** Hugging Face Datasets v4.8.4 source code — `arrow_dataset.py`, `io/parquet.py`, `packaged_modules/parquet/parquet.py`, `config.py`

---

## 1. What is from_parquet?

`Dataset.from_parquet()` is a **static method** on the Hugging Face `Dataset` class that creates a Dataset directly from one or more Parquet files. Unlike `load_dataset()` (which downloads and processes an entire dataset repository), `from_parquet()` works on local files, remote URIs, or `hf://` paths — no dataset repository metadata required.

```python
from datasets import Dataset

# Single local file
ds = Dataset.from_parquet("data/train.parquet")

# Multiple files (auto-concatenated)
ds = Dataset.from_parquet(["data/shard-01.parquet", "data/shard-02.parquet"])

# Remote URI (HF Hub, S3, GCS)
ds = Dataset.from_parquet("hf://datasets/username/repo/data/train-00000-of-00001.parquet")
```

## 2. Full API Surface

### 2.1 Signature (v4.8.4)

```python
@staticmethod
def from_parquet(
    path_or_paths: Union[PathLike, list[PathLike]],
    split: Optional[NamedSplit] = None,
    features: Optional[Features] = None,
    cache_dir: str = None,
    keep_in_memory: bool = False,
    columns: Optional[list[str]] = None,
    num_proc: Optional[int] = None,
    filters: Optional[Union[pds.Expression, list[tuple], list[list[tuple]]]] = None,
    fragment_scan_options: Optional[pds.ParquetFragmentScanOptions] = None,
    on_bad_files: Literal["error", "warn", "skip"] = "error",
    **kwargs,
) -> "Dataset":
```

### 2.2 Parameters In Detail

| Parameter | Type | Default | Since | Description |
|-----------|------|---------|-------|-------------|
| `path_or_paths` | `PathLike` or `list[PathLike]` | required | — | Local path, remote URI, or list thereof |
| `split` | `NamedSplit` | `None` | — | Split name to assign (useful for later train/test split) |
| `features` | `Features` | `None` | — | Schema override; auto-inferred from Parquet if `None` |
| `cache_dir` | `str` | `None` | — | Override default cache dir (`~/.cache/huggingface/datasets`) |
| `keep_in_memory` | `bool` | `False` | — | Copy data to memory instead of memory-mapping Arrow on disk |
| `columns` | `list[str]` | `None` | — | Column projection — only load these columns (supports nested prefixes) |
| `num_proc` | `int` | `None` | 2.8.0 | Multi-process download/generation for multi-file datasets |
| `filters` | `Expression`, `list[tuple]`, or `list[list[tuple]]` | `None` | — | Predicate pushdown; skips non-matching row groups |
| `fragment_scan_options` | `ParquetFragmentScanOptions` | `None` | 4.2.0 | Cache/buffering tuning for remote Parquet |
| `on_bad_files` | `"error"`, `"warn"`, `"skip"` | `"error"` | 4.2.0 | How to handle corrupt/invalid Parquet files |

### 2.3 Also Accepts `**kwargs` → ParquetConfig

Additional kwargs are forwarded to `ParquetConfig`, which supports:
- `batch_size` — override row group batch size
- `streaming` — when using `load_dataset` with Parquet, but NOT for `from_parquet()` directly (use `read()` with `streaming=True` on the reader)

## 3. Internal Architecture

### 3.1 Call Flow

```
Dataset.from_parquet(paths)
  └─→ ParquetDatasetReader(paths, ...)
        ├─ read() — builds dataset
        │     ├─ streaming=True → Parquet.as_streaming_dataset(split)
        │     └─ streaming=False → Parquet.download_and_prepare() + .as_dataset()
        └─ Parquet (ArrowBasedBuilder)
              └─ _generate_tables(files, row_groups_list)
                    └─ PyArrow ParquetFileFormat.make_fragment(file)
                          └─ .subset(row_group_ids)  ← row group sharding
                                └─ .to_batches(columns=, filter=, batch_size=)
                                      └─ pa.Table.from_batches([batch])
                                            └─ _cast_table(table)  ← features casting
```

### 3.2 Row Group Sharding (Performance Key)

The `Parquet._generate_more_gen_kwargs()` method is where the magic happens. Instead of loading an entire Parquet file at once, it:

1. Opens the file with `ParquetFileFormat.make_fragment(file)`
2. Iterates through **each row group** individually: `(0,), (1,), (2,), ...`
3. Each row group becomes its own `(file, row_groups)` tuple
4. For streaming, this means each row group is loaded on demand

This enables **incremental loading** and **memory efficiency** — large Parquet files with many row groups are processed one row group at a time.

```python
# Pseudocode of _generate_more_gen_kwargs:
parquet_fragment = parquet_file_format.make_fragment(file)
num_rg = parquet_fragment.num_row_groups
for rg_id in range(num_rg):
    yield {"files": [file], "row_groups_list": [(rg_id,)]}
```

### 3.3 Filter Pushdown Architecture

When `filters=` is provided, the pipeline converts it to a PyArrow `dataset.Expression`:

```python
filter_expr = (
    pq.filters_to_expression(self.config.filters)  # list → Expression
    if isinstance(self.config.filters, list)
    else self.config.filters  # already Expression
)

# Then passed to fragment.to_batches(filter=filter_expr, ...)
```

**Filter formats accepted:**
- `pyarrow.dataset.Expression` — e.g., `ds.field("col") > 0`
- `list[tuple]` — AND semantics: `[("age", ">=", 18), ("active", "==", True)]`
- `list[list[tuple]]` — DNF (OR-of-ANDs): `[[("age", "<", 13)], [("age", ">=", 65)]]`

**Pushdown mechanism:** PyArrow's `to_batches(filter=...)` uses Parquet's **row group column statistics** (min/max values per row group) to skip entire row groups when the filter cannot match. This means:
- For remote files: only row groups with matching data are downloaded
- For local files: only matching row groups are decompressed

### 3.4 Column Projection

When `columns=` is specified, only the selected column chunks are read from Parquet:

```python
# This reads only col_0 and col_1 from each row group
parquet_fragment.to_batches(columns=["col_0", "col_1"])
```

**Nested prefix support:** A column name acts as a prefix — `"a"` selects `a.b`, `a.c`, and `a.d.e`.

**Combined with features:** If both `columns` and `features` are set, they must match — otherwise a `ValueError` is raised in `Parquet._info()`.

### 3.5 Bad File Handling (v4.2.0+)

Three modes for handling corrupt Parquet files when loading multiple files:

| Mode | Behaviour |
|------|-----------|
| `"error"` (default) | Raise `pa.ArrowInvalid` on first bad file |
| `"warn"` | Log a warning and skip the bad file |
| `"skip"` | Silently skip bad files |

Schema inference skips bad files in all modes:
```python
for file in files:
    try:
        with open(file, "rb") as f:
            self.info.features = Features.from_arrow_schema(pq.read_schema(f))
            break  # First valid schema wins
    except pa.ArrowInvalid:
        if on_bad_files == "error": raise
        # else continue to next file
```

### 3.6 FragmentScanOptions (v4.2.0+)

For remote Parquet files, you can tune HTTP request behavior:

```python
import pyarrow.dataset as ds
import pyarrow as pa

fragment_scan_options = ds.ParquetFragmentScanOptions(
    cache_options=pa.CacheOptions(
        prefetch_limit=1,       # Number of fragments to prefetch
        range_size_limit=128 << 20,  # Max range request size in bytes (128 MiB)
    ),
)

ds = Dataset.from_parquet(
    "hf://datasets/.../*.parquet",
    fragment_scan_options=fragment_scan_options,
)
```

Default `range_size_limit` is 32 MiB. Increasing it to 128 MiB reduces the number of HTTP range requests for large columns at the cost of potential over-fetching.

## 4. to_parquet() — The Write Side

### 4.1 Signature

```python
def to_parquet(
    self,
    path_or_buf: Union[PathLike, BinaryIO],
    batch_size: Optional[int] = None,
    storage_options: Optional[dict] = None,
    **parquet_writer_kwargs,
) -> int:
```

### 4.2 Writer Architecture

Uses `PyArrow ParquetWriter` with **intelligent defaults**:

```python
writer = pq.ParquetWriter(
    file_obj,
    schema=schema,
    use_content_defined_chunking=self.use_content_defined_chunking,
    write_page_index=True,  # Enables page-level skipping in readers
    compression={
        col: "none" if require_storage_embed(feature) else "snappy"
        for col, feature in dataset.features.items()
    },
    use_dictionary=[
        col for col, feature in dataset.features.items()
        if not require_storage_embed(feature)
    ],
    column_encoding={
        col: "PLAIN" for col, feature in dataset.features.items()
        if require_storage_embed(feature)
    },
)
```

**Compression strategy per column type:**
| Column Type | Compression | Encoding | Dictionary |
|-------------|-------------|----------|------------|
| Normal (text, numbers, bool) | Snappy | auto | Yes |
| Media (Image, Audio, Binary) | None | PLAIN | No |

### 4.3 Content-Defined Chunking (CDC)

Enabled by default. Splits row groups at content-defined boundaries:

```python
DEFAULT_CDC_OPTIONS = {
    "min_chunk_size": 256 * 1024,     # 256 KB
    "max_chunk_size": 1024 * 1024,     # 1 MB
    "norm_level": 0,
}
```

CDC metadata is persisted in the Parquet file:
```python
writer.add_key_value_metadata({
    "content_defined_chunking": json.dumps(self.use_content_defined_chunking)
})
```

Pass `use_content_defined_chunking=False` to disable CDC and use PyArrow's default row group sizing.

### 4.4 Batch Size Tuning

Defaults are auto-computed:

```python
self.batch_size = (
    batch_size  # explicit override
    or get_writer_batch_size_from_features(dataset.features)
    or get_writer_batch_size_from_data_size(len(dataset), dataset._estimate_nbytes())
)
```

The target row group size is `MAX_ROW_GROUP_SIZE = "100MB"` (uncompressed).

### 4.5 Remote URI Writing

Supports writing to any fsspec-compatible backend:

```python
# Write to HF Hub
ds.to_parquet("hf://datasets/username/repo/data/train.parquet")

# Write to S3
ds.to_parquet("s3://my-bucket/data/train.parquet",
              storage_options={"key": "...", "secret": "..."})

# Write to GCS
ds.to_parquet("gs://my-bucket/data/train.parquet")
```

The `storage_options` dict is passed to fsspec's `open()`.

## 5. Streaming with Parquet

While `from_parquet()` always returns a **map-style** `Dataset` (materialized on disk/memory), you can stream Parquet via `load_dataset()` with `streaming=True`:

```python
from datasets import load_dataset

ds = load_dataset(
    "parquet",
    data_files="hf://datasets/.../*.parquet",
    streaming=True,
    split="train",
)
```

In streaming mode, row groups are loaded lazily — only when iterated. Filter pushdown and column projection still work in streaming mode, skipping non-matching row groups before downloading.

## 6. Integration with Hub Datasets Server

When a dataset on the Hub has Parquet files on its `refs/convert/parquet` branch, you can load them directly:

```python
import requests
import duckdb

# Get Parquet URLs from Datasets Server
resp = requests.get(
    "https://datasets-server.huggingface.co/parquet",
    params={"dataset": "username/dataset-name"},
).json()

urls = [pf["url"] for pf in resp["parquet_files"]]

# Load via datasets library
ds = Dataset.from_parquet(urls)

# Or query directly with DuckDB (zero-cost analytics)
result = duckdb.sql("""
    SELECT COUNT(*), AVG(score)
    FROM read_parquet(urls)
    WHERE text IS NOT NULL
""").fetchall()
```

## 7. Performance Patterns

### 7.1 Column Projection First
```python
# GOOD: only reads 3 columns from disk
ds = Dataset.from_parquet("large.parquet", columns=["id", "text", "label"])

# BAD: reads all columns into Arrow, then drops
ds = Dataset.from_parquet("large.parquet")
ds = ds.select_columns(["id", "text", "label"])
```

### 7.2 Filter Pushdown Before Load
```python
# GOOD: row group metadata skips non-matching data
ds = Dataset.from_parquet("large.parquet", filters=[("year", ">=", 2024)])

# BAD: loads everything, then filters
ds = Dataset.from_parquet("large.parquet")
ds = ds.filter(lambda x: x["year"] >= 2024)
```

### 7.3 Sharded Parallel Loading
```python
from datasets import Dataset
from glob import glob

# Multi-file with parallel processing
files = sorted(glob("data/shard-*.parquet"))
ds = Dataset.from_parquet(files, num_proc=4)
```

### 7.4 Remote Parquet with Caching
```python
fragment_scan_options = ds.ParquetFragmentScanOptions(
    cache_options=pa.CacheOptions(
        prefetch_limit=2,
        range_size_limit=64 << 20,  # 64 MiB
    ),
)
ds = Dataset.from_parquet(
    urls,
    columns=["text", "label"],
    filters=[("label", "in", [0, 1])],
    fragment_scan_options=fragment_scan_options,
)
```

### 7.5 Write Optimized Parquet for Future Reads
```python
# When writing, optimize row groups for future fast reading
ds.to_parquet(
    "output.parquet",
    row_group_size=100_000,   # ~10-50 MB per group
    write_page_index=True,     # Enable page-level skipping
    use_content_defined_chunking=False,  # Simpler row groups
    compression="zstd",        # Better compression ratio than snappy
)
```

## 8. Config Constants Reference

| Constant | Value | Purpose |
|----------|-------|---------|
| `USE_PARQUET_EXPORT` | `True` | Enable/disable Parquet export globally |
| `DEFAULT_CDC_OPTIONS` | `{"min_chunk_size": 262144, "max_chunk_size": 1048576, "norm_level": 0}` | Content-defined chunking parameters |
| `MAX_ROW_GROUP_SIZE` | `"100MB"` | Target uncompressed row group size |
| `PARQUET_ROW_GROUP_SIZE_FOR_AUDIO_DATASETS` | `None` | Audio-specific override |
| `PARQUET_ROW_GROUP_SIZE_FOR_IMAGE_DATASETS` | `None` | Image-specific override |
| `PARQUET_ROW_GROUP_SIZE_FOR_BINARY_DATASETS` | `None` | Binary-specific override |
| `PARQUET_ROW_GROUP_SIZE_FOR_VIDEO_DATASETS` | `None` | Video-specific override |

## 9. Key Design Decisions

1. **Row-group-at-a-time sharding**: Parquet doesn't load entire files — it iterates individual row groups, making even massive files manageable.

2. **Schema from first valid file**: Only the first readable Parquet file's schema is used for feature inference; subsequent files are cast to match.

3. **Arrow on disk, not in memory**: By default, `from_parquet()` creates memory-mapped Arrow files on disk. Data is only loaded into RAM when accessed. `keep_in_memory=True` copies into RAM for hot workloads.

4. **CDC vs traditional row groups**: CDC creates content-defined boundaries (256KB-1MB) that are more stable across data changes than PyArrow's default row group sizing. Pass `use_content_defined_chunking=False` for simpler row group boundaries.

5. **Bad file tolerance**: With `on_bad_files="warn"` or `"skip"`, loading continues past corrupt files. This is crucial when loading large sharded datasets where individual shards may be corrupted.

## 10. Sources

- Source code: `src/datasets/arrow_dataset.py` — `from_parquet()` line 1491, `to_parquet()` line 5625
- Source code: `src/datasets/io/parquet.py` — `ParquetDatasetReader`, `ParquetDatasetWriter`
- Source code: `src/datasets/packaged_modules/parquet/parquet.py` — `ParquetConfig`, `Parquet._generate_tables()`
- Source code: `src/datasets/config.py` — `MAX_ROW_GROUP_SIZE`, `DEFAULT_CDC_OPTIONS`, `USE_PARQUET_EXPORT`
- Source code: `src/datasets/features/features.py` — `require_storage_embed()` for media column detection
- PyArrow docs: `pyarrow.dataset.ParquetFragmentScanOptions`, `pyarrow.CacheOptions`
