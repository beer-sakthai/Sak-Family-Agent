---
name: SakThai-hf-datasets-server-rest-api
description: "HF Datasets Server REST API — browse, query, search, filter, and download datasets on the Hub without downloading the full dataset. Covers all 11+ endpoints, pagination, auth, and integration patterns."
---

# HF Datasets Server REST API

The **Datasets Server** (`https://datasets-server.huggingface.co`) provides a free REST API for exploring 100,000+ datasets on the Hugging Face Hub without downloading them. It auto-converts datasets to Parquet for analytics frameworks.

## Base URL

```
https://datasets-server.huggingface.co
```

No API key required for public datasets. Gated/private datasets need authentication via `Authorization: Bearer $HF_TOKEN` header.

## Endpoints

### 1. Check dataset validity — `GET /is-valid`

```bash
curl "https://datasets-server.huggingface.co/is-valid?dataset=wikimedia/wikipedia"
```

Response: `{"preview":true,"viewer":true,"search":true,"filter":true,"statistics":true}`

### 2. List splits and subsets — `GET /splits`

```bash
curl "https://datasets-server.huggingface.co/splits?dataset=wikimedia/wikipedia"
```

Returns all configs (subsets) and splits with their row counts.

### 3. Get dataset information — `GET /info`

```bash
curl "https://datasets-server.huggingface.co/info?dataset=wikimedia/wikipedia&config=20231101.en"
```

Returns dataset card metadata, features (columns with dtypes), dataset size info, and splits.

### 4. Preview a dataset — `GET /first-rows`

```bash
curl "https://datasets-server.huggingface.co/first-rows?dataset=wikimedia/wikipedia&config=20231101.en&split=train"
```

Returns the first 100 rows with feature definitions and row count.

### 5. Download slices of rows — `GET /rows`

```bash
curl "https://datasets-server.huggingface.co/rows?dataset=wikimedia/wikipedia&config=20231101.en&split=train&offset=100&length=50"
```

Parameters:
- `offset`: Starting row index (default: 0)
- `length`: Number of rows to return (default: 100, max: 100)

### 6. Search text — `GET /search`

```bash
curl "https://datasets-server.huggingface.co/search?dataset=wikimedia/wikipedia&config=20231101.en&split=train&query=anarchism&offset=0&length=10"
```

Parameters:
- `query`: Search term (scanned across all text columns)
- `offset` / `length`: Pagination

### 7. Filter rows — `GET /filter`

```bash
curl "https://datasets-server.huggingface.co/filter?dataset=...&config=...&split=train&where=..."
```

Parameters:
- `where`: SQL-like filter expression (e.g., `id=12`)

### 8. List Parquet files — `GET /parquet`

```bash
curl "https://datasets-server.huggingface.co/parquet?dataset=wikimedia/wikipedia&config=20231101.en"
```

Returns Parquet file URLs for analytics processing (Pandas, Polars, DuckDB, PySpark, etc.).

### 9. Get dataset size — `GET /size`

```bash
curl "https://datasets-server.huggingface.co/size?dataset=wikimedia/wikipedia"
```

Returns `num_rows`, `num_bytes_parquet_files`, `num_bytes_memory` per config/split.

### 10. Explore statistics — `GET /statistics`

```bash
curl "https://datasets-server.huggingface.co/statistics?dataset=wikimedia/wikipedia&config=20231101.en&split=train"
```

Returns column-level statistics (min, max, mean, std, histogram for numeric columns).

### 11. Get Croissant metadata — `GET /croissant`

```bash
curl "https://datasets-server.huggingface.co/croissant?dataset=wikimedia/wikipedia&config=20231101.en"
```

Returns ML-Commons Croissant metadata for dataset interoperability.

## Authentication

Add a header for gated/private datasets:

```bash
curl -H "Authorization: Bearer hf_xxxx" "https://datasets-server.huggingface.co/rows?dataset=some/private-dataset&config=default&split=train"
```

## Pagination

All list endpoints support:
- `offset` — row index to start from (0-indexed)
- `length` — rows per page (default/limit: 100 for `/rows`, varies for `/search`)

## Integration Patterns

### Python with `huggingface_hub`

```python
from huggingface_hub import HfApi
api = HfApi()

# List configs/splits
splits = api.get_dataset_splits("wikimedia/wikipedia")
print(splits.splits)

# Get info
info = api.dataset_info("wikimedia/wikipedia", config="20231101.en")

# Get first rows
rows = api.get_dataset_first_rows("wikimedia/wikipedia", config="20231101.en", split="train")
for row in rows.rows:
    print(row.row.title)
```

### Python with raw requests

```python
import requests

BASE = "https://datasets-server.huggingface.co"

# Get size of a dataset
resp = requests.get(f"{BASE}/size?dataset=wikimedia/wikipedia").json()
for s in resp["sizes"]:
    print(f"{s['config']}/{s['split']}: {s['num_rows']} rows, {s['num_bytes_memory']/1e6:.0f} MB")

# Get rows with pagination
resp = requests.get(
    f"{BASE}/rows",
    params={"dataset": "wikimedia/wikipedia", "config": "20231101.en", "split": "train", "offset": 0, "length": 5}
).json()
for row in resp["rows"]:
    print(row["row"]["title"])
```

### Query Parquet files with DuckDB

```bash
# Get Parquet URLs first
curl -s "https://datasets-server.huggingface.co/parquet?dataset=wikimedia/wikipedia&config=20231101.en" \
  | jq -r '.parquet_files[].url' > parquet_urls.txt

# Query with DuckDB
duckdb -c "SELECT title, length(text) AS text_len FROM read_parquet('$(head -1 parquet_urls.txt)') LIMIT 5"
```

### Query Parquet files with Pandas

```python
import pandas as pd
import requests

resp = requests.get("https://datasets-server.huggingface.co/parquet?dataset=wikimedia/wikipedia&config=20231101.en").json()
urls = [f["url"] for f in resp["parquet_files"]]

# Load first Parquet file
df = pd.read_parquet(urls[0])
print(df.head())
```

### Query Parquet files with Polars

```python
import polars as pl

# Load all Parquet files directly
df = pl.scan_parquet("hf://datasets/wikimedia/wikipedia/20231101.en/train/*.parquet")
# or via URLs from /parquet endpoint
```

## Reference: Live API Examples

See [`references/live-api-examples.md`](references/live-api-examples.md) for verified response sizes, real API output, pagination patterns, and the "renamed dataset" pitfall documented with exact failure cases.

## Reference: Analytics Querying with Parquet

See [`references/analytics-parquet-querying.md`](references/analytics-parquet-querying.md) for DuckDB, Polars, and Pandas patterns for querying HF Datasets Server Parquet files — predicate pushdown, streaming, cross-dataset JOINs, and the `hf://` protocol.

## See Also

- [`hf-datasets-library`](..) — Python `datasets` library internals: Arrow memory mapping, cache, `Dataset.map()`, and local processing. Use when you need to manipulate datasets beyond simple exploration.

## Rate Limits

The Datasets Server is a free public service. For heavy usage or production applications, consider:
- Caching responses locally
- Adding retry logic with backoff
- Using Parquet file downloads for large-scale analytics instead of `/rows`

## Key Facts

- Auto-converts every dataset on the Hub to Parquet behind the scenes
- Responses are pre-computed and cached — instant response times
- Covers 100,000+ datasets
- No auth needed for public datasets
- `/is-valid` checks which features (preview, search, filter, statistics) are enabled for a dataset
- Some older datasets may return `"The dataset has been renamed"` — use the current name from the Hub

## Pitfalls

- **Renamed datasets**: Many classic datasets (imdb, tiny_shakespeare, openbookqa, tweet_eval) have been renamed. Use the current name from `hf.co/datasets`.
- **Large text cells**: `/rows` and `/first-rows` return full cell content; very long text fields can make responses large. Use `offset`/`length` for pagination.
- **Search timeout**: The `/search` endpoint may time out on very large datasets. For production, download Parquet files and use DuckDB/Polars for search.
- **No CORS issues**: The API supports CORS for browser-based clients.
- **Config required**: Many endpoints need a `config` (subset) parameter — use `/splits` first to discover available configs.
