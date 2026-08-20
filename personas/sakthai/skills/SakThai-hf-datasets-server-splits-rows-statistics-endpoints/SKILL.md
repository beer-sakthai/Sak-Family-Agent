---
name: SakThai-hf-datasets-server-splits-rows-statistics-endpoints
description: '>-   Deep-dive into the remaining Datasets Server REST API endpoints beyond the   well-known
  filter/search/parquet APIs: /splits, /first-rows, /rows, /size,   /statistics, /is-valid,
  and /siblings.  Each endpoint is documented with the   exact reques'
---

# HF Datasets Server — Splits, Rows, Statistics Endpoints (Deep Dive)

## Overview

The Hugging Face Datasets Server at `https://datasets-server.huggingface.co`
provides a **zero-install, RESTful API** for exploring and querying datasets
hosted on the Hub.  While the search, filter, and parquet-conversion endpoints
are well documented, the **splits, rows, size, statistics, is-valid, and
siblings** endpoints are equally important for programmatic dataset
introspection.  They let an agent (or script) discover a dataset's structure,
preview its content, and understand its size and column statistics **without
ever downloading a single Parquet file**.

## Endpoint Reference

### 1. `/splits` — List Available Splits and Configurations

**Method:** GET  
**Required param:** `dataset` (string, dataset identifier on the Hub)  
**Example:** `GET /splits?dataset=dair-ai/emotion`

**Response schema:**
```json
{
  "splits": [
    {
      "dataset": "dair-ai/emotion",
      "config": "split",
      "split": "train"
    },
    { "dataset": "dair-ai/emotion", "config": "split", "split": "validation" },
    { "dataset": "dair-ai/emotion", "config": "split", "split": "test" },
    { "dataset": "dair-ai/emotion", "config": "unsplit", "split": "train" }
  ],
  "pending": [],
  "failed": []
}
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `splits[].dataset` | string | Dataset identifier |
| `splits[].config` | string | Configuration/subset name |
| `splits[].split` | string | Split name (train/validation/test, etc.) |
| `pending` | string[] | Configs being processed |
| `failed` | string[] | Configs that failed to load |

**Use case:** Discover the structure of a dataset before deciding which config
and split to query.  For datasets with many configs (e.g. `wikimedia/wikipedia`
has 300+ language configs), this is the first step in any pipeline.

**Errors:**
- `404` — Dataset not found, renamed, or private
- Returns `{"error": "..."}` with descriptive message

---

### 2. `/first-rows` — Preview First Rows

**Method:** GET  
**Required params:** `dataset`, `config`, `split`  
**Example:** `GET /first-rows?dataset=dair-ai/emotion&config=split&split=train`

**Response schema (abbreviated):**
```json
{
  "dataset": "dair-ai/emotion",
  "config": "split",
  "split": "train",
  "features": [
    { "feature_idx": 0, "name": "text", "type": { "dtype": "string", "_type": "Value" } },
    { "feature_idx": 1, "name": "label", "type": { "names": ["sadness","joy","love","anger","fear","surprise"], "_type": "ClassLabel" } }
  ],
  "rows": [
    { "row_idx": 0, "row": { "text": "i didnt feel humiliated", "label": 0 }, "truncated_cells": [] },
    { "row_idx": 1, "row": { "text": "i can go from feeling so hopeless to so damned hopeful...", "label": 0 }, "truncated_cells": [] }
  ]
}
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `features[]` | object[] | Column schema with name, type, dtype |
| `features[].type` | object | Can be `Value(dtype)`, `ClassLabel(names)`, `Sequence`, `Array2D/3D/4D/5D`, `Image`, `Audio`, etc. |
| `rows[]` | object[] | Row data, limited to ~100 rows |
| `rows[].truncated_cells` | string[] | Cell names truncated due to size limits |

**Notes:**
- Returns the **first ~100 rows** of the split (the server decides the exact
  limit; typically 100)
- The `features` array is a flat schema — nested structures (Sequence, Struct)
  are flattened.  For the full nested schema you need the `parquet` endpoint.
- `truncated_cells` lists which cell values were truncated (large images,
  long text, audio blobs)

**Use case:** Quickly inspect the schema and see sample data.  This is the
fastest way to understand column types, class labels, and data format without
loading the dataset.

---

### 3. `/rows` — Get Arbitrary Row Ranges

**Method:** GET  
**Required params:** `dataset`, `config`, `split`  
**Optional params:** `offset` (int, default 0), `length` (int, default 100)  
**Example:** `GET /rows?dataset=dair-ai/emotion&config=split&split=train&offset=0&length=3`

**Response schema:**
```json
{
  "features": [ ... ],
  "rows": [
    { "row_idx": 0, "row": { "text": "...", "label": 0 }, "truncated_cells": [] },
    { "row_idx": 1, "row": { "text": "...", "label": 0 }, "truncated_cells": [] },
    { "row_idx": 2, "row": { "text": "...", "label": 3 }, "truncated_cells": [] }
  ],
  "num_rows_total": 16000,
  "num_rows_per_page": 100
}
```

**Fields (additional to first-rows):**
| Field | Type | Description |
|-------|------|-------------|
| `num_rows_total` | int | Total rows in this split |
| `num_rows_per_page` | int | Max rows returned per request (typically 100) |

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `offset` | int | 0 | Starting row index |
| `length` | int | 100 | Number of rows to return (max typically 100) |

**Use case:** Page through a dataset programmatically.  Combine with `offset`
and `length` to iterate over all rows in batches.

---

### 4. `/size` — Dataset Size Information

**Method:** GET  
**Required param:** `dataset`  
**Optional param:** `config` (filter to one config)  
**Example:** `GET /size?dataset=dair-ai/emotion`

**Response schema:**
```json
{
  "size": {
    "dataset": {
      "dataset": "dair-ai/emotion",
      "num_bytes_original_files": 28175731,
      "num_bytes_parquet_files": 28175731,
      "num_bytes_memory": 49362934,
      "num_rows": 436809,
      "estimated_num_rows": null
    },
    "configs": [
      {
        "dataset": "dair-ai/emotion",
        "config": "split",
        "num_bytes_original_files": 1287193,
        "num_bytes_parquet_files": 1287193,
        "num_bytes_memory": 2223504,
        "num_rows": 20000,
        "num_columns": 2,
        "estimated_num_rows": null
      },
      {
        "dataset": "dair-ai/emotion",
        "config": "unsplit",
        "num_bytes_original_files": 26888538,
        "num_bytes_parquet_files": 26888538,
        "num_bytes_memory": 47139430,
        "num_rows": 416809,
        "num_columns": 2,
        "estimated_num_rows": null
      }
    ]
  }
}
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `size.dataset.num_bytes_original_files` | int | Total bytes of original source files |
| `size.dataset.num_bytes_parquet_files` | int | Bytes of converted Parquet files |
| `size.dataset.num_bytes_memory` | int | Estimated bytes when loaded in memory (Python objects) |
| `size.dataset.num_rows` | int | Total row count across all configs |
| `configs[].num_bytes_*` | int | Per-config size breakdown |
| `configs[].num_columns` | int | Number of columns in this config |

**Use case:** Decide whether a dataset is feasible to load in-memory.  If
`num_bytes_memory` exceeds available RAM, use streaming or query server-side.
Also useful for cost estimation of processing pipelines.

---

### 5. `/statistics` — Column-level Statistics

**Method:** GET  
**Required params:** `dataset`, `config`, `split`  
**Example:** `GET /statistics?dataset=dair-ai/emotion&config=split&split=train`

**Response schema (abbreviated):**
```json
{
  "num_examples": 16000,
  "statistics": [
    {
      "column_name": "label",
      "column_type": "class_label",
      "column_statistics": {
        "nan_count": 0,
        "nan_proportion": 0.0,
        "no_label_count": 0,
        "no_label_proportion": 0.0,
        "n_unique": 6,
        "frequencies": {
          "sadness": 4666,
          "joy": 5362,
          "love": 1304,
          "anger": 2159,
          "fear": 1937,
          "surprise": 572
        }
      }
    },
    {
      "column_name": "text",
      "column_type": "string_text",
      "column_statistics": {
        "nan_count": 0,
        "nan_proportion": 0.0,
        "min": 7,
        "max": 300,
        "mean": 96.84581,
        "median": 86.0,
        "std": 55.90495,
        "histogram": {
          "hist": [1833, 3789, 3616, ...],
          "bucket_edges": [7.0, 36.3, 65.6, ...]
        }
      }
    }
  ]
}
```

**Column types and their statistics:**

| Column Type | Statistics Provided |
|-------------|-------------------|
| `class_label` | nan_count, n_unique, frequencies (map) |
| `string_text` | nan_count, min, max, mean, median, std, histogram (10 buckets) |
| `int` | nan_count, min, max, mean, median, std, histogram |
| `float` | nan_count, min, max, mean, median, std, histogram |
| `bool` | nan_count, frequencies (true/false counts) |
| `audio` | nan_count (no waveform stats) |
| `image` | nan_count (no pixel stats) |

**Use case:** Understand data distributions before training.  Check class
balance, text length distributions, feature ranges.  This is the cheapest way
to do EDA (exploratory data analysis) on a dataset — no download needed.

---

### 6. `/is-valid` — Dataset Viewer Availability

**Method:** GET  
**Required param:** `dataset`  
**Example:** `GET /is-valid?dataset=dair-ai/emotion`

**Response schema:**
```json
{
  "preview": true,
  "viewer": true,
  "search": true,
  "filter": true,
  "statistics": true
}
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `preview` | bool | `/first-rows` endpoint available |
| `viewer` | bool | Dataset viewer UI available |
| `search` | bool | `/search` endpoint available |
| `filter` | bool | `/filter` endpoint available |
| `statistics` | bool | `/statistics` endpoint available |

**Use case:** Check if a dataset is queryable via the Datasets Server *before*
making further API calls.  If `viewer` is false, the dataset is either too
large, not supported, or not yet converted to Parquet.

---

### 7. `/siblings` — Dataset File Listing

**Method:** GET  
**Required param:** `dataset`  
**Example:** `GET /siblings?dataset=dair-ai/emotion`

**Note:** This endpoint returned "Not Found" during testing (2026-07-25).
It may have been deprecated or replaced.  The preferred way to list dataset
files is the Hugging Face Hub API:
`GET https://huggingface.co/api/datasets/{dataset}` which includes a `siblings`
array.

---

## Practical Patterns

### Pattern 1: Autonomous Dataset Discovery

```python
import httpx
from huggingface_hub import HfApi

api = HfApi()
DATASETS_SERVER = "https://datasets-server.huggingface.co"

def discover_dataset(dataset_id: str) -> dict:
    """Discover a dataset's structure without loading it."""
    # 1. Check validity
    valid = httpx.get(f"{DATASETS_SERVER}/is-valid", params={"dataset": dataset_id}).json()
    if not valid.get("viewer"):
        return {"error": "Dataset not available via viewer"}
    
    # 2. Get splits
    splits = httpx.get(f"{DATASETS_SERVER}/splits", params={"dataset": dataset_id}).json()
    
    # 3. Get size info
    size = httpx.get(f"{DATASETS_SERVER}/size", params={"dataset": dataset_id}).json()
    
    # 4. Get first rows of first split (schema preview)
    first_config = splits["splits"][0]["config"]
    first_split = splits["splits"][0]["split"]
    rows = httpx.get(f"{DATASETS_SERVER}/first-rows", params={
        "dataset": dataset_id, "config": first_config, "split": first_split
    }).json()
    
    return {
        "valid": valid,
        "splits": splits,
        "size": size,
        "features": rows.get("features", []),
        "sample_rows": rows.get("rows", [])[:3]
    }
```

### Pattern 2: Class Balance Check

```python
def check_class_balance(dataset_id: str, config: str, split: str = "train"):
    """Get class distribution for a labeled dataset."""
    stats = httpx.get(f"{DATASETS_SERVER}/statistics", params={
        "dataset": dataset_id, "config": config, "split": split
    }).json()
    
    for col_stat in stats.get("statistics", []):
        if col_stat["column_type"] == "class_label":
            freq = col_stat["column_statistics"]["frequencies"]
            total = sum(freq.values())
            return {
                "column": col_stat["column_name"],
                "distribution": {k: {"count": v, "pct": round(v/total*100, 1)} 
                                 for k, v in sorted(freq.items(), key=lambda x: -x[1])}
            }
    return {"error": "No class_label column found"}
```

### Pattern 3: Paginated Row Access

```python
def iter_rows(dataset_id: str, config: str, split: str, page_size: int = 100):
    """Generator yielding all rows from a dataset split."""
    offset = 0
    while True:
        resp = httpx.get(f"{DATASETS_SERVER}/rows", params={
            "dataset": dataset_id, "config": config, "split": split,
            "offset": offset, "length": page_size
        }).json()
        
        if "rows" not in resp:
            break
        
        for row in resp["rows"]:
            yield row["row"]
        
        offset += len(resp["rows"])
        if offset >= resp.get("num_rows_total", 0):
            break
```

## Known Limitations

1. **No `/siblings` endpoint** — As tested on 2026-07-25, the siblings
   endpoint returns "Not Found".  Use the Hub API for file listings.
2. **Row pagination limit** — Maximum rows per request is ~100.  Large-scale
   data access should use the `/parquet` endpoint for bulk downloads.
3. **Statistics limited to one split** — Must call per split; no aggregate
   statistics across all splits.
4. **Feature schema flattening** — Nested types (e.g. Sequence of Struct) are
   flattened.  The full arrow schema is available via `/parquet` metadata.
5. **No authentication** for private datasets — All endpoints require the
   dataset to be public or the viewer to be configured for gated access.
6. **Histogram buckets** — String histograms use 10 fixed buckets with
   character-count-based edges.
