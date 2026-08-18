---
name: SakThai-hf-datasets-parquet-column-selection
description: 'Deep reference on Parquet column projection, filter pushdown, predicate pushdown,
  row group skipping, and column pruning with Hugging Face Datasets. Covers Dataset.from_parquet(),
  Dataset.to_parquet(), ParquetConfig, PyArrow dataset integration, fragment scan
  options, content-defined chunking, and practical zero-cost analytics query patterns
  via DuckDB, Polars, and direct Parquet reads.

  '
---

# SakThai — HF Datasets Parquet Column Selection & Filter Pushdown Deep Dive

## Charge: Optimal (full flow)

This skill is the definitive reference on Parquet column selection and
predicate pushdown in the Hugging Face Datasets library.

---

## 1. Two API Surfaces

HF Datasets provides **two** ways to read Parquet, each with different
column-selection and filtering capabilities:

| API | Method | Column Projection | Filter Pushdown | Streaming |
|-----|--------|-------------------|-----------------|-----------|
| **High-level** | `Dataset.from_parquet()` | `columns=` param | `filters=` param (auto-pushed to PyArrow) | `streaming=True` |
| **Low-level** | `load_dataset("parquet", data_files=...)` | `ParquetConfig.columns` | `ParquetConfig.filters` | `streaming=True` |

Both map to the same internal `Parquet` builder class in
`src/datasets/packaged_modules/parquet/parquet.py`.

---

## 2. Column Projection (columns=)

### How it works

When `columns=["col_a", "col_c"]` is passed:
1. The `ParquetConfig` stores it as `self.config.columns`
2. In `_split_generators()`, features are filtered to only include requested columns
3. In `_generate_tables()`, the columns list is passed to `parquet_fragment.to_batches(columns=self.config.columns, ...)`
4. **PyArrow only reads the requested column chunks from disk** — row group statistics for skipped columns are never loaded
5. The resulting `pa.Table` only contains the projected columns

### Nesting support

Column names may be prefixes of nested fields. `columns=["a"]` selects `a.b`, `a.c`, and `a.d.e`.

### Performance impact

| Action | With column projection | Without |
|--------|----------------------|---------|
| Disk I/O | Only projected columns | All columns |
| Memory | Projected data only | Full dataset |
| Row group scan | Reads stats for projected columns only | All column stats |

**Rule of thumb:** Always specify `columns=` unless you need all fields. For
text-heavy datasets, skipped columns can reduce memory 5-50×.

### Example: Column projection

```python
# Load only 2 columns from a 100-column Parquet file
ds = Dataset.from_parquet("data.parquet", columns=["title", "id"])
```

---

## 3. Filter Pushdown (filters=)

### How it works

When `filters=[("col_a", "==", 0)]` is passed:

1. The filter list is converted to a `pyarrow.dataset.Expression` via `pq.filters_to_expression()`
2. The expression is passed to `parquet_fragment.to_batches(filter=filter_expr, ...)`
3. **PyArrow uses Parquet row group statistics (min/max/null counts) to skip entire row groups** whose stats prove no row can match
4. Only row groups that *could* contain matching rows are decoded
5. Within surviving row groups, the filter is applied at the record-batch level

### Filter format

Three formats accepted:

| Format | Example | Use case |
|--------|---------|----------|
| `pyarrow.dataset.Expression` | `ds.field("age") > 18` | Complex conjunctions |
| `list[tuple]` (DNF) | `[("age", ">", 18), ("name", "==", "Alice")]` | AND conditions |
| `list[list[tuple]]` (DNF) | `[[("age", ">", 18)], [("name", "==", "Alice")]]` | OR of ANDs |

Internally lists are converted to expressions via `pq.filters_to_expression()`.

### Row group skipping in practice

Row groups typically contain 100K–1M rows. Each row group stores:
- Column chunk metadata (type, encoding, offset, compressed/uncompressed size)
- **Column statistics** (min, max, null_count, distinct_count, is_sorted)

When a filter on `age > 18` is applied, PyArrow checks each row group's `age`
column chunk: if `max(age) <= 18`, the entire row group (100K+ rows) is
skipped with zero decompression or decoding.

### Fragment scan options

Added in Datasets v4.2.0. Control buffering and caching:

```python
import pyarrow.dataset as ds

scan_opts = ds.ParquetFragmentScanOptions(
    cache_options=pa.CacheOptions(
        prefetch_limit=1,
        range_size_limit=128 << 20  # 128 MiB minimum request size
    ),
)

ds = Dataset.from_parquet(
    "data.parquet",
    filters=[("year", ">=", 2024)],
    fragment_scan_options=scan_opts,
)
```

---

## 4. Internal Architecture

### ParquetConfig (dataclass)

```python
@dataclass
class ParquetConfig(datasets.BuilderConfig):
    batch_size: Optional[int] = None          # Row group size default
    columns: Optional[list[str]] = None       # Column projection
    features: Optional[datasets.Features] = None  # Cast to features
    filters: Optional[Union[ds.Expression, list[tuple], list[list[tuple]]]] = None
    fragment_scan_options: Optional[ds.ParquetFragmentScanOptions] = None
    on_bad_files: Literal["error", "warn", "skip"] = "error"
```

### Reading flow

```
Dataset.from_parquet()
  └─ ParquetDatasetReader
       └─ Parquet builder
            ├─ _split_generators() → infers features from arrow schema
            ├─ _generate_more_gen_kwargs() → splits into per-row-group shards
            └─ _generate_tables() → core scanning loop
                 ├─ filters → pq.filters_to_expression()
                 ├─ parquet_fragment.to_batches(columns=, filter=)
                 └─ yield → _cast_table() → Dataset
```

### Writing flow

```
Dataset.to_parquet()
  └─ ParquetDatasetWriter
       ├─ Uses pq.ParquetWriter with content-defined chunking
       ├─ Batch-size auto-tuning via MAX_ROW_GROUP_SIZE (100MB default)
       ├─ Compression: snappy for regular cols, none for binary media (Image/Audio)
       └─ Writes CDC metadata as key-value metadata
```

---

## 5. Content-Defined Chunking (CDC)

Datasets v3+ uses **content-defined chunking** by default for Parquet writing.
This splits Parquet row groups at content-defined boundaries (not fixed offsets),
improving deduplication and compression.

```python
config.DEFAULT_CDC_OPTIONS = {
    "min_chunk_size": 256 * 1024,    # 256 KiB
    "max_chunk_size": 1024 * 1024,   # 1 MiB
    "norm_level": 0,
}
```

Pass `use_content_defined_chunking=False` or a custom dict to `to_parquet()`.

---

## 6. Streaming + Filters

When `streaming=True` is combined with filters, the filter pushdown works
**identically** — row groups are skipped at the Parquet metadata level before
any data is streamed.

```python
# Downloads 0% of non-matching row groups
ds = Dataset.from_parquet(
    "hf://datasets/big/dataset/data/*.parquet",
    streaming=True,
    filters=[("year", ">=", 2024)],
    columns=["title", "year"],
)

for row in ds:
    print(row["title"])  # Only matching rows, projected columns
```

---

## 7. Column Selection for Nested Types

Nested types (struct, list) require special handling:

```python
# For struct columns, select the top-level name
ds = Dataset.from_parquet("data.parquet", columns=["metadata"])

# For list columns, selecting the list name loads all elements
ds = Dataset.from_parquet("data.parquet", columns=["embeddings"])
```

Arrow's zero-copy reads mean selecting a list column only loads the offsets
array and the data buffer, not the entire column's decoded Python objects.

---

## 8. Zero-Cost External Query Patterns

For analytics where you don't need a `Dataset` object:

### DuckDB — predicate pushdown via Parquet statistics

```python
import duckdb

con = duckdb.connect()
con.execute(f"""
    SELECT title, count(*) as cnt
    FROM read_parquet('hf://datasets/big/data/*.parquet')
    WHERE year >= 2024
    GROUP BY title
    ORDER BY cnt DESC
    LIMIT 10
""").fetchdf()
```

DuckDB parses Parquet statistics natively and pushes predicates down to
row-group level — same mechanism as PyArrow but with SQL interface.

### Polars — lazy column projection

```python
import polars as pl

lf = pl.scan_parquet("hf://datasets/big/data/*.parquet")
result = (
    lf
    .select(["title", "year"])   # column projection at scan
    .filter(pl.col("year") >= 2024)
    .collect(streaming=True)     # out-of-core processing
)
```

### hf:// protocol direct access

```python
# Bypass the datasets library entirely
import polars as pl

df = pl.scan_parquet("hf://datasets/username/dataset/split/*.parquet")
```

Requires `HF_TOKEN` env var for gated datasets.

---

## 9. Performance Benchmarks (Conceptual)

| Workload | Columns | Filter | Without projection | With projection | Speedup |
|----------|---------|--------|-------------------|-----------------|---------|
| 10M rows, 100 cols, heavy text | `["id"]` | None | 12s (all cols) | 0.3s (1 col) | 40× |
| 10M rows, 100 cols | `["id","year"]` | `year>2020` | 8s (scan + filter) | 1.2s (prune + pushdown) | 6.7× |
| Streaming 50GB dataset | `["text"]` | `lang=="en"` | OOM | 800MB peak | Memory-safe |

---

## 10. Key Constants

| Constant | Default | Location |
|----------|---------|----------|
| `MAX_ROW_GROUP_SIZE` | `"100MB"` | `datasets/config.py` |
| `DEFAULT_CDC_OPTIONS` | `{min: 256KB, max: 1MB}` | `datasets/config.py` |
| `DEFAULT_MAX_BATCH_SIZE` | 1000 | `datasets/config.py` |
| `USE_PARQUET_EXPORT` | `True` | `datasets/config.py` |
| `PARQUET_ROW_GROUP_SIZE_FOR_AUDIO_DATASETS` | `None` | `datasets/config.py` |
| `PARQUET_ROW_GROUP_SIZE_FOR_IMAGE_DATASETS` | `None` | `datasets/config.py` |
| `PARQUET_ROW_GROUP_SIZE_FOR_BINARY_DATASETS` | `None` | `datasets/config.py` |

---

## 11. Pitfalls

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| **columns/features mismatch** | `ValueError` on load | Ensure projected columns match features |
| **Empty filter result** | Query returns 0 rows | Check row group stats vs filter ranges |
| **on_bad_files='error'** | Stops on first corrupt file | Use `'skip'` for robustness |
| **No filter pushdown with `or`** | Full table scan | PyArrow only pushes simple conjunctions |
| **CDC metadata bloat** | Large Parquet metadata | Disable CDC for small datasets |
