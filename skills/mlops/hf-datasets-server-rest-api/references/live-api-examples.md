# Datasets Server — Live API Examples

**Verified:** 2026-07-23 against `wikimedia/wikipedia` (en subset, 6.4M rows)
**Base URL:** `https://datasets-server.huggingface.co`

## Response Sizes

| Endpoint | Params | Size/Notes |
|----------|--------|------------|
| `/splits?dataset=wikimedia/wikipedia` | — | ~340 language configs, each with 1 split (train). ~12KB |
| `/first-rows?dataset=wikimedia/wikipedia&config=20231101.en&split=train` | — | 100 rows returned. ~296KB response (large text cells) |
| `/rows?dataset=wikimedia/wikipedia&config=20231101.en&split=train&offset=0&length=2` | offset=0, length=2 | 2 rows. ~72KB (each article text is large) |
| `/size?dataset=wikimedia/wikipedia` | — | All configs, each with num_rows, num_bytes_parquet_files, num_bytes_memory. ~85KB |
| `/parquet?dataset=wikimedia/wikipedia&config=20231101.en` | — | 41 Parquet files, ~200MB–600MB each. ~8KB |
| `/is-valid?dataset=wikimedia/wikipedia` | — | Tiny: `{"preview":true,"viewer":true,"search":true,"filter":true,"statistics":true}` |

## Key Observations

### 1. Large text cells blow up response size
The `/first-rows` endpoint for Wikipedia returned **296KB for just 100 rows** because each article's full text is included. When working with text-heavy datasets, always use `/rows` with small `length` values and paginate.

### 2. `/size` is the cheapest way to assess a dataset
```json
{
  "dataset": "wikimedia/wikipedia",
  "sizes": [
    {
      "dataset": "wikimedia/wikipedia",
      "config": "20231101.en",
      "split": "train",
      "num_bytes_parquet_files": 11229098508,  // ~11 GB
      "num_bytes_memory": 65885260988,          // ~66 GB
      "num_rows": 6407814,                      // 6.4 million
      "num_columns": 4,
      "estimated_num_rows": null
    }
  ]
}
```
Use this before deciding to download a dataset. The ratio `num_bytes_memory / num_rows` tells you how heavy each row is (~10KB/row for Wikipedia English).

### 3. `/parquet` gives analytics-ready URLs
```json
{
  "parquet_files": [
    {
      "dataset": "wikimedia/wikipedia",
      "config": "20231101.en",
      "split": "train",
      "url": "https://huggingface.co/datasets/wikimedia/wikipedia/resolve/refs%2Fconvert%2Fparquet/20231101.en/train/0000.parquet",
      "filename": "0000.parquet",
      "size": 420296449
    }
  ]
}
```
41 shards for English Wikipedia. You can load these directly into DuckDB/Polars/Pandas without downloading the dataset through `datasets` library.

### 4. Many classic datasets return "The dataset has been renamed"
Tested and confirmed failing:
- `imdb` → renamed
- `tiny_shakespeare` → renamed
- `openbookqa` → renamed
- `tweet_eval` → renamed
- `bigcode/the-stack-smol` → "does not exist or is not accessible without authentication"

The Datasets Server references current Hub names. Use `hf datasets list` or browse `hf.co/datasets` to find the current name.

### 5. `/rows` response structure
```json
{
  "features": [
    {"feature_idx": 0, "name": "id", "type": {"dtype": "string", "_type": "Value"}},
    {"feature_idx": 1, "name": "url", "type": {"dtype": "string", "_type": "Value"}},
    {"feature_idx": 2, "name": "title", "type": {"dtype": "string", "_type": "Value"}},
    {"feature_idx": 3, "name": "text", "type": {"dtype": "string", "_type": "Value"}}
  ],
  "rows": [
    {
      "row_idx": 0,
      "row": {"id": "12", "url": "https://en.wikipedia.org/wiki/Anarchism", "title": "Anarchism", "text": "..."},
      "truncated_cells": []
    }
  ],
  "num_rows_total": 6407814,
  "num_rows_per_page": 100,
  "partial": false
}
```

### 6. No auth for public datasets
All public datasets returned data without any `Authorization` header. For gated/private datasets, add: `-H "Authorization: Bearer hf_..."`
