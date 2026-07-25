# Analytics Querying of HF Datasets Server Parquet Files

**Verified:** 2026-07-23 against HF datasets-server docs
**Base URL:** `https://datasets-server.huggingface.co`
**Parquet API:** `https://huggingface.co/api/datasets/{dataset}/parquet`

> Complements the main SKILL.md by focusing on analytics/workload querying patterns
> instead of raw REST API endpoints. Covers DuckDB, Polars, Pandas, and the `hf://` protocol.

## Background

The datasets server auto-converts every public dataset on the Hub (≤5GB) to
Parquet on a special `refs/convert/parquet` branch. For datasets already in
Parquet, it links original files unless row groups exceed ~300MB. These
Parquet files are analytics-ready and can be queried directly without the
`datasets` library.

**Key property:** Parquet is columnar — only the columns you request are read
from disk (projection pushdown), and row-group-level statistics (min/max/null
counts) enable automatic partition pruning.

## Getting Parquet URLs

### Via datasets-server REST API

```bash
curl "https://datasets-server.huggingface.co/parquet?dataset=wikimedia/wikipedia&config=20231101.en"
```

Response: `{"parquet_files": [{"dataset":"...","config":"...","split":"train","url":"https://...","filename":"0000.parquet","size":420296449}]}`

### Via HF Hub API (cleaner structure)

```bash
curl "https://huggingface.co/api/datasets/ibm/duorc/parquet"
```

Returns `{config: {split: [urls]}}` grouped by config and split. Also supports
per-split narrowing: `/api/datasets/{ds}/parquet/{config}/{split}`.

### Via Python

```python
import requests

def get_parquet_urls(dataset: str, config: str | None = None, split: str | None = None) -> list[str]:
    """Fetch Parquet file URLs for a HF dataset."""
    if config and split:
        url = f"https://huggingface.co/api/datasets/{dataset}/parquet/{config}/{split}"
        return requests.get(url).json()  # list of URLs
    url = f"https://huggingface.co/api/datasets/{dataset}/parquet"
    resp = requests.get(url).json()
    urls = []
    for cfg, splits in resp.items():
        for sp, file_urls in splits.items():
            if config and cfg != config:
                continue
            if split and sp != split:
                continue
            urls.extend(file_urls)
    return urls
```

## DuckDB

DuckDB can query Parquet files directly from HTTP URLs — no download needed.

### Basic query

```python
import duckdb

# Single Parquet URL
url = "https://huggingface.co/datasets/wikimedia/wikipedia/resolve/refs%2Fconvert%2Fparquet/20231101.en/train/0000.parquet"

con = duckdb.connect()
result = con.execute(f"""
    SELECT title, length(text) AS text_len
    FROM read_parquet('{url}')
    WHERE title LIKE '%Machine learning%'
    LIMIT 10
""").fetchdf()

print(result)
```

### Query multiple shards

```python
import requests, duckdb

# Get all Parquet URLs for a split
resp = requests.get(
    "https://huggingface.co/api/datasets/wikimedia/wikipedia/parquet/20231101.en/train"
).json()

# Wrap in duckdb's read_parquet which accepts lists or glob patterns
urls = resp  # list of URL strings
con = duckdb.connect()
con.execute(f"""
    CREATE VIEW wiki AS
    SELECT * FROM read_parquet({urls});
""")

# Predicate pushdown: DuckDB pushes WHERE clauses into Parquet metadata
stats = con.execute("""
    SELECT
        count(*) AS total_rows,
        avg(length(text)) AS avg_text_len,
        max(length(text)) AS max_text_len
    FROM wiki
    WHERE title IS NOT NULL
""").fetchdf()
print(stats)
```

### SQL JOIN across datasets

```python
# Load Parquet from two different datasets
urls_a = requests.get("https://huggingface.co/api/datasets/dataset-a/parquet/default/train").json()
urls_b = requests.get("https://huggingface.co/api/datasets/dataset-b/parquet/default/train").json()

con = duckdb.connect()
con.execute(f"CREATE VIEW a AS SELECT * FROM read_parquet({urls_a})")
con.execute(f"CREATE VIEW b AS SELECT * FROM read_parquet({urls_b})")

# JOIN on shared key
result = con.execute("""
    SELECT a.id, a.title, b.score
    FROM a JOIN b ON a.id = b.id
    WHERE b.score > 0.9
    LIMIT 100
""").fetchdf()
```

### Performance tips for DuckDB + HF Parquet

| Technique | Why | How |
|-----------|-----|-----|
| **Column selection** | Avoid reading large text columns | `SELECT title, url FROM ...` not `SELECT *` |
| **Limit pushdown** | Stop scanning early | `LIMIT N` reduces scanned row groups |
| **WHERE on stats columns** | Row-group pruning | Filter on columns with sorted/distinct values |
| **Parquet glob** | Query all shards simply | `read_parquet('https://.../*.parquet')` |
| **Memory limit** | Prevent OOM on large datasets | `SET memory_limit = '2GB'` |

## Polars

Polars is a Rust-based DataFrame library with lazy evaluation and excellent
Parquet support.

### Basic query

```python
import polars as pl
import requests

# Get Parquet URLs
urls = requests.get(
    "https://huggingface.co/api/datasets/wikimedia/wikipedia/parquet/20231101.en/train"
).json()

# Lazy scan — reads schema only, defers data loading
lf = pl.scan_parquet(urls)

# Build query plan (lazy — nothing executed yet)
query = (lf
    .filter(pl.col("title").str.contains("Machine learning"))
    .select(["title", "url", pl.col("text").str.len_bytes().alias("text_len")])
    .top_k(10, by="text_len")
)

# Execute
result = query.collect()
print(result)
```

### Streaming for large datasets

```python
# Process in streaming mode to avoid OOM
lf = pl.scan_parquet(urls)

result = (lf
    .select(["title", "id"])
    .group_by("id")
    .agg(pl.col("title").count())
    .sort("title", descending=True)
    .collect(streaming=True)  # <-- streaming mode
)
```

### Predicate pushdown verification

Polars pushes supported filters to the Parquet reader. You can verify:

```python
lf = pl.scan_parquet(urls)
plan = lf.filter(pl.col("title") == "Anarchism").describe_optimized_plan()
print(plan)  # Shows filter pushed down to Parquet scan
```

## Pandas

Pandas can read Parquet URLs directly but loads everything into memory.

```python
import pandas as pd
import requests

urls = requests.get(
    "https://huggingface.co/api/datasets/wikimedia/wikipedia/parquet/20231101.en/train"
).json()

# Read first shard only (Pandas can't glob HTTP URLs easily)
df = pd.read_parquet(urls[0], columns=["title", "url", "text"])
print(df.head())
```

**⚠ Warning:** Pandas loads the entire file into memory. For datasets with
large text cells (like Wikipedia), even one shard (~300MB on disk) can
expand to several GB in memory. Prefer DuckDB or Polars for large datasets.

## Using `hf://` protocol

The `huggingface_hub` library supports an `hf://` filesystem protocol for
direct Parquet access:

```python
import polars as pl

# Requires: pip install huggingface_hub polars
df = pl.scan_parquet("hf://datasets/wikimedia/wikipedia/20231101.en/train/*.parquet")
result = df.filter(pl.col("title") == "Anarchism").collect()
```

This bypasses the datasets-server API entirely and reads from the Hub's
storage directly. Requires `HF_TOKEN` for gated datasets.

## When to use which approach

| Use case | Best tool | Why |
|----------|-----------|-----|
| **Ad-hoc SQL queries** | DuckDB | SQL interface, fast, no Python overhead |
| **Large dataset ETL** | Polars (streaming) | Lazy eval, OOM-safe, expression API |
| **Quick exploration** | Pandas | Familiar, small/medium datasets only |
| **Multi-dataset JOIN** | DuckDB | Cross-dataset SQL JOINs |
| **Complex transformations** | Polars | Expressions are more expressive than SQL |
| **Minimal dependencies** | DuckDB | Single binary, no Python needed |

## Dataset size estimation before querying

Always check dataset size first via `/size`:

```bash
curl "https://datasets-server.huggingface.co/size?dataset=wikimedia/wikipedia"
```

Key metrics per config/split:
- `num_rows` — total rows
- `num_bytes_parquet_files` — compressed size on disk
- `num_bytes_memory` — estimated in-memory size (can be 5-10× larger for text)

If `num_bytes_memory` exceeds available RAM, use DuckDB with `memory_limit`
or Polars with `streaming=True`.

## Pitfalls

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| **Huge text cells in memory** | OOM crash | Don't `SELECT *` on text-heavy datasets; use DuckDB with projected columns |
| **Parquet HTTP timeout** | Connection reset on large files | Use `duckdb` with `SET threads TO 1` for single-connection reads |
| **Polars HTTP glob 404** | `No such file or directory` | Use explicit URL list from `/api/parquet` instead of glob |
| **hf:// auth required** | Permission denied | Set `HF_TOKEN` env var for gated datasets |
| **Partial datasets** | Missing rows in query | Check `partial: true` in `/parquet` response; only first 5GB converted |
| **Renamed datasets** | `{"error":"The dataset has been renamed"}` | Use current Hub name from `hf.co/datasets` |
