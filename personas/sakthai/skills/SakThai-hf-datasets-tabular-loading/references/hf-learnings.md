# HF Learnings: hf-datasets-tabular-loading-comprehensive

**Date:** 2026-07-25
**Topic:** Comprehensive deep-dive into loading tabular and text data with the 🤗 Datasets library

## Summary

Covers the full surface of loading tabular data (CSV, Pandas DataFrames, HDF5, SQL databases) and text data (plain text, XML, JSON, JSONL) using the Hugging Face Datasets library. Includes format-specific configurations, multi-file patterns, streaming optimization, column selection, and best practices for each source type.

---

## 1. CSV Files

### Basic Loading
```python
from datasets import load_dataset

# Single file
dataset = load_dataset("csv", data_files="my_file.csv")

# Multiple files (auto-concatenated)
dataset = load_dataset("csv", data_files=["file1.csv", "file2.csv", "file3.csv"])

# Split mapping
dataset = load_dataset("csv", data_files={
    "train": ["train1.csv", "train2.csv"],
    "test": "test.csv"
})
```

### Remote CSV Files
```python
base_url = "https://huggingface.co/datasets/lhoestq/demo1/resolve/main/data/"
dataset = load_dataset('csv', data_files={
    "train": base_url + "train.csv",
    "test": base_url + "test.csv"
})
```

### Zipped CSV Files
```python
url = "https://domain.org/train_data.zip"
dataset = load_dataset("csv", data_files={"train": url})
```

### CSV Configuration Options

The CSV loader accepts a `CsvConfig` with these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `delimiter` | str | `,` | Field delimiter |
| `quotechar` | str | `"` | Quoting character |
| `escapechar` | str | `None` | Escape character |
| `doublequote` | bool | `True` | Handle double quotes inside quoted fields |
| `skipinitialspace` | bool | `False` | Skip whitespace after delimiter |
| `header` | bool/int | `0` | Row index for column names, or `None` for no header |
| `skip_blank_lines` | bool | `True` | Skip empty lines |
| `comment` | str | `None` | Comment character (lines starting with this are ignored) |
| `encoding` | str | `utf-8` | File encoding |
| `compression` | str | `None` | Compression type ("gzip", "bz2", "xz", "zstd") |

**Example with custom config:**
```python
dataset = load_dataset(
    "csv",
    data_files="file.csv",
    delimiter=";",
    header=0,
    encoding="latin-1",
    compression="gzip"
)
```

---

## 2. JSON / JSONL Files

### JSON Lines (default)
Each line is a JSON object — the most common format for ML datasets:
```python
dataset = load_dataset("json", data_files="data.jsonl")
```

### JSON Array (single file with list)
Use `field` parameter to specify which field contains the data array:
```python
dataset = load_dataset("json", data_files="data.json", field="data")
```

### Multi-file JSON patterns
```python
# Glob pattern
dataset = load_dataset("json", data_files="en/c4-train.0000*-of-01024.json.gz")

# Explicit list
dataset = load_dataset("json", data_files=["a.jsonl", "b.jsonl", "c.jsonl"])

# Split mapping
dataset = load_dataset("json", data_files={
    "train": "train.jsonl",
    "test": "test.jsonl"
})
```

### JSON Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `field` | str | `None` | JSON field containing the data array |
| `encoding` | str | `utf-8` | File encoding |
| `compression` | str | `None` | Compression type |
| `chunksize` | int | `10 << 20` | Read chunk size in bytes (10 MB default) |

---

## 3. Pandas DataFrames

### from_pandas()
```python
from datasets import Dataset
import pandas as pd

df = pd.read_csv("data.csv")
dataset = Dataset.from_pandas(df)

# With split name
train_ds = Dataset.from_pandas(train_df, split="train")
test_ds = Dataset.from_pandas(test_df, split="test")

# Preserve index
dataset = Dataset.from_pandas(df, preserve_index=True)
```

### Important Caveats

- Pandas `Series` may not carry enough type info for Arrow inference
- DataFrames of length `0` or with `None/NaN` values default to `null` type
- **Solution:** Explicitly specify features:
```python
from datasets import Features, Value

features = Features({
    "text": Value("string"),
    "label": Value("int32")
})
dataset = Dataset.from_pandas(df, features=features)
```

### Performance Note
`from_pandas()` is slower than loading directly from files because it converts through Arrow. For large datasets, prefer loading from CSV/JSON/Parquet directly with `load_dataset()`.

---

## 4. HDF5 Files

HDF5 is used for large numerical datasets in scientific computing:
```python
dataset = load_dataset("hdf5", data_files="data.h5")
```

**Assumption:** All datasets in the HDF5 file have the same number of rows on their first dimension (tabular structure).

---

## 5. SQL Databases

### SQLite
```python
from datasets import Dataset

# Load entire table
ds = Dataset.from_sql("table_name", "sqlite:///database.db")

# Load from SQL query
ds = Dataset.from_sql(
    'SELECT * FROM states WHERE state="California";',
    "sqlite:///database.db"
)
```

**URI format:** `sqlite:///path/to/database.db`

### PostgreSQL
Same `from_sql()` method works with PostgreSQL URIs:
```python
ds = Dataset.from_sql("table_name", "postgresql://user:pass@host:port/dbname")
```

### SQL URI Patterns by Database

| Database | URI Format |
|----------|------------|
| SQLite | `sqlite:///path/to/db.sqlite` |
| PostgreSQL | `postgresql://user:pass@host:port/dbname` |
| MySQL | `mysql://user:pass@host:port/dbname` |
| DuckDB | `duckdb:///path/to/db.duckdb` |

**Caching:** SQL queries are cached. Re-querying the same URI returns the cached result.

---

## 6. Text Files

### Line-by-line (default)
```python
dataset = load_dataset("text", data_files={"train": "train.txt", "test": "test.txt"})
```

### Sampling by paragraph or document
```python
# Each paragraph is one example
dataset = load_dataset("text", data_files="file.txt", sample_by="paragraph")

# Each document (separated by blank lines) is one example
dataset = load_dataset("text", data_files="file.txt", sample_by="document")
```

### Loading from a directory
```python
dataset = load_dataset("text", data_dir="path/to/text/dataset")
```

### Grep patterns for file selection
```python
c4_subset = load_dataset("allenai/c4", data_files="en/c4-train.0000*-of-01024.json.gz")
```

### Remote text files via HTTP
```python
dataset = load_dataset("text", data_files="https://example.org/data/train.txt")
```

### XML Files
```python
# XML loader = "text" loader with sample_by="document"
dataset = load_dataset("xml", data_files={"train": ["file1.xml", "file2.xml"]})

# Load from directory
dataset = load_dataset("xml", data_dir="path/to/xml/dataset")
```

---

## 7. Key Parameters Across All Loaders

### streaming (bool, default=False)
When `True`, returns an `IterableDataset` instead of `Dataset`. Data is loaded lazily as you iterate. Essential for datasets too large for disk.

```python
dataset = load_dataset("csv", data_files="huge.csv", streaming=True)
```

### split (str, default=None)
Select a specific split. When `data_files` is a dict, uses the keys as split names automatically. Use `split="train"` to select a named split.

### columns (list, default=None)
Select only specific columns at load time. Saves memory for columnar formats (Parquet, Arrow) by only reading needed columns:

```python
dataset = load_dataset("csv", data_files="data.csv", columns=["id", "text"])
```

### data_dir (str, default=None)
Directory containing data files. Auto-discovers files when combined with the appropriate builder name.

### data_files (str/list/dict)
Explicit file specification. Supports:
- Single file: `"file.csv"`
- List: `["a.csv", "b.csv"]`
- Dict with split keys: `{"train": "train.csv", "test": "test.csv"}`
- Glob patterns: `"data/*.jsonl"`

### compression (str, default=None)
Force compression detection: `"gzip"`, `"bz2"`, `"xz"`, `"zstd"`. Auto-detected from file extension if `None`.

### num_proc (int, default=None)
Number of processes for parallel loading/conversion. Only applies to non-streaming mode.

---

## 8. Memory Optimization Patterns

### Streaming for large files
```python
ds = load_dataset("csv", data_files="very_large.csv", streaming=True)
for example in ds:
    process(example)
```

### Column subset selection (non-streaming, memory-mapped)
```python
# Only load specific columns — the rest stay as Arrow on disk
ds = load_dataset("csv", data_files="wide_table.csv", columns=["col_a", "col_b"])
```

### Chunked reading (streaming)
Break a large IterableDataset into manageable chunks:
```python
ds = load_dataset("json", data_files="huge.jsonl", streaming=True)
chunk = ds.take(1000)  # first 1000 examples
for example in chunk:
    process(example)
```

### Converting existing Dataset to IterableDataset (faster than streaming=true)
```python
# Faster: download first (non-streaming), then convert to iterable
ds = load_dataset("dataset_name", split="train")
iterable_ds = ds.to_iterable_dataset(num_shards=64)
```

---

## 9. Error Handling Patterns

### File not found
```python
try:
    ds = load_dataset("csv", data_files="nonexistent.csv")
except FileNotFoundError as e:
    print(f"Data file not found: {e}")
```

### Encoding issues
```python
# Try common encodings
for enc in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
    try:
        ds = load_dataset("csv", data_files="file.csv", encoding=enc)
        break
    except UnicodeDecodeError:
        continue
```

### Malformed JSON/CSV
Use streaming to handle errors per-row:
```python
ds = load_dataset("json", data_files="possibly_malformed.jsonl", streaming=True)
def safe_iter(ds):
    for i, example in enumerate(ds):
        try:
            yield example
        except Exception as e:
            print(f"Skipping row {i}: {e}")
            continue
```

---

## 10. Best Practices Summary

| Use Case | Recommended Approach |
|----------|---------------------|
| Small CSV (<1 GB) | `load_dataset("csv", data_files=...)` |
| Large CSV (>1 GB) | `load_dataset("csv", data_files=..., streaming=True)` |
| Many small CSV files | `load_dataset("csv", data_files=glob_pattern)` |
| Pandas DataFrame | `Dataset.from_pandas(df)` |
| SQL query result | `Dataset.from_sql(query, uri)` |
| JSONL streaming | `load_dataset("json", data_files=..., streaming=True)` |
| Text line-by-line | `load_dataset("text", data_files=...)` |
| XML documents | `load_dataset("xml", data_files=...)` |
| HDF5 numerical data | `load_dataset("hdf5", data_files=...)` |
| Production training | Non-streaming + `to_iterable_dataset(num_shards=N)` |

---

## Resources

- Official docs: https://huggingface.co/docs/datasets/en/loading
- Tabular loading: https://huggingface.co/docs/datasets/en/tabular_load
- Text loading: https://huggingface.co/docs/datasets/en/nlp_load
- Streaming: https://huggingface.co/docs/datasets/en/stream
- Map-style vs Iterable: https://huggingface.co/docs/datasets/en/about_mapstyle_vs_iterable
- Dataset class reference: https://huggingface.co/docs/datasets/en/package_reference/main_classes
