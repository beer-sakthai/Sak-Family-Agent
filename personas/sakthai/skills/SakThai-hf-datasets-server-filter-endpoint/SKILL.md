---
name: SakThai-hf-datasets-server-filter-endpoint
description: ">   Complete reference for the Hugging Face Datasets Server /filter endpoint \u2014\
  \   covering DuckDB SQL WHERE syntax, supported operators, column type handling,\
  \   partial indexing for large datasets, ORDER BY, pagination, related endpoints\
  \   (statistics"
---

# HF Datasets Server `/filter` Endpoint: DuckDB SQL Filtering Reference

## Overview

The Datasets Server provides a **`/filter`** endpoint for filtering dataset rows
server-side using DuckDB SQL expressions. Unlike `/rows` (which returns raw
row slices), `/filter` applies a `WHERE` clause before returning rows — so you
can query for exactly the data you need without downloading the full dataset.

**Prerequisites:** Only datasets with **Parquet exports** are supported, since
the server needs indexed Parquet files to run queries without downloading the
whole dataset.

### Base URL

```
https://datasets-server.huggingface.co/filter
```

### Parameters

| Parameter  | Required | Type    | Default | Description |
|------------|----------|---------|---------|-------------|
| `dataset`  | ✅ Yes   | string  | —       | Dataset name (e.g., `nyu-mll/glue`) |
| `config`   | ✅ Yes   | string  | —       | Dataset configuration/subset name (e.g., `sst2`) |
| `split`    | ✅ Yes   | string  | —       | Split name (e.g., `train`, `validation`, `test`) |
| `where`    | ✅ Yes   | string  | —       | DuckDB SQL WHERE condition (URL-encoded) |
| `offset`   | ❌ No    | integer | 0       | Row offset for pagination (>= 0) |
| `length`   | ❌ No    | integer | 100     | Max rows to return (0–100) |
| `orderby`  | ❌ No    | string  | —       | ORDER BY clause (DuckDB SQL, e.g., `"idx" ASC`) |

### Response

```json
{
  "rows": [
    {
      "row_idx": 0,
      "row": { "sentence": "text here", "label": 1, "idx": 0 },
      "truncated_cells": []
    }
  ],
  "num_rows_total": 67349,
  "partial": false,
  "features": [
    { "feature_idx": 0, "name": "sentence", "type": { "dtype": "string", "_type": "Value" } },
    { "feature_idx": 1, "name": "label",    "type": { "names": ["negative", "positive"], "_type": "ClassLabel" } },
    { "feature_idx": 2, "name": "idx",      "type": { "dtype": "int32", "_type": "Value" } }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `rows` | array | Array of row objects with `row_idx`, `row` (column->value dict), `truncated_cells` |
| `num_rows_total` | int | Total number of rows matching the filter (approximate for partial results) |
| `partial` | bool | `true` if only first 5GB was indexed (large datasets) |
| `features` | array | Column schema — feature definitions with name and type info |

---

## 2. WHERE Clause Syntax (DuckDB SQL)

### Column Name Rules

- Column names must be enclosed in **double quotes**: `"column_name"`
- This is required by DuckDB SQL (though unquoted names sometimes work in simple cases)

### Value Format Rules

| Column Type   | Value Format              | Example                                     |
|---------------|---------------------------|---------------------------------------------|
| Numeric (int, float) | Unquoted number    | `"idx" = 42`, `"score" >= 3.14`            |
| String        | Single-quoted string      | `"sentence" = 'exact text'`                |
| ClassLabel    | Integer index (0-based)   | `"label" = 0` (maps to first label name)   |
| Bool          | `true` / `false` (lowercase) | `"is_valid" = true`                     |

### Supported Operators

| Operator | Description | Works? | Example |
|----------|-------------|--------|---------|
| `=` | Equality | ✅ | `"label" = 1` |
| `!=` | Inequality | ✅ | `"idx" != 0` |
| `<` | Less than | ✅ | `"idx" < 100` |
| `>` | Greater than | ✅ | `"score" > 0.5` |
| `<=` | Less than or equal | ✅ | `"idx" <= 100` |
| `>=` | Greater than or equal | ✅ | `"idx" >= 100` |
| `LIKE` | Pattern match (case-insensitive, `%` wildcard) | ✅ | `"sentence" LIKE '%love%'` |
| `GLOB` | Pattern match (case-sensitive, `*` wildcard) | ✅ | `"sentence" GLOB '*love*'` |
| `IS NULL` | Null check | ✅ | `"sentence" IS NULL` |
| `IS NOT NULL` | Not-null check | ✅ | `"sentence" IS NOT NULL` |
| `AND` | Logical AND | ✅ | `"label" = 1 AND "sentence" LIKE '%funny%'` |
| `OR` | Logical OR | ✅ | `"idx" < 5 OR "idx" > 67340` |
| `IN` | Membership test | ❌ | `"idx" IN (1, 2, 3)` — unsupported |
| `NOT` | Logical NOT (prefix) | ❌ | `NOT "idx" = 0` — unsupported |
| `BETWEEN` | Range test | ❌ | `"idx" BETWEEN 1 AND 10` — unsupported |

### String Equality vs LIKE

- **`=`** with single quotes matches **exact** strings (including trailing spaces)
- **`LIKE`** with `%` wildcards matches **patterns** (case-insensitive by SQL standard)
- **`GLOB`** with `*` wildcards matches **patterns** (case-sensitive)

### Quoting Special Characters

- If a string value contains a single quote, escape it with `''` (two single quotes)
- Example: `"sentence" = 'don''t stop'`
- Column names with special characters: always use double quotes: `"my-column"`

---

## 3. Practical Filter Patterns

### Basic Numeric Filter

```python
import requests

response = requests.get(
    "https://datasets-server.huggingface.co/filter",
    params={
        "dataset": "nyu-mll/glue",
        "config": "sst2",
        "split": "train",
        "where": '"idx" >= 100 AND "idx" < 105',
        "offset": 0,
        "length": 10,
    }
)
data = response.json()
print(f"Found {data['num_rows_total']} rows (partial: {data['partial']})")
for row in data["rows"]:
    print(row["row"]["sentence"])
```

### String Pattern Match

```python
# Find all rows containing "love" in the sentence
response = requests.get(
    "https://datasets-server.huggingface.co/filter",
    params={
        "dataset": "nyu-mll/glue",
        "config": "sst2",
        "split": "train",
        "where": '"sentence" LIKE \'%love%\'',
        "length": 20,
    }
)
data = response.json()
print(f"Total matches: {data['num_rows_total']}")  # e.g., 1027
```

### Exact String Match

```python
response = requests.get(
    "https://datasets-server.huggingface.co/filter",
    params={
        "dataset": "nyu-mll/glue",
        "config": "sst2",
        "split": "train",
        "where": '"sentence" = \'hide new secretions from the parental units \'',
    }
)
data = response.json()
print(f"Exact matches: {data['num_rows_total']}")  # 1
```

### ClassLabel Filter (by Integer Index)

```python
# "label" is ClassLabel with names ["negative", "positive"]
# Filter for positive reviews (label=1)
response = requests.get(
    "https://datasets-server.huggingface.co/filter",
    params={
        "dataset": "nyu-mll/glue",
        "config": "sst2",
        "split": "train",
        "where": '"label" = 1 AND "sentence" LIKE \'%amazing%\'',
        "length": 5,
    }
)
```

### Filter with ORDER BY

```python
# Get the last 5 rows (highest idx) that match a pattern
response = requests.get(
    "https://datasets-server.huggingface.co/filter",
    params={
        "dataset": "nyu-mll/glue",
        "config": "sst2",
        "split": "train",
        "where": '"sentence" LIKE \'%the%\'',
        "orderby": '"idx" DESC',
        "length": 5,
    }
)
```

### Pagination Through Results

```python
page = 0
page_size = 100  # max per request
total = None

while total is None or page * page_size < total:
    response = requests.get(
        "https://datasets-server.huggingface.co/filter",
        params={
            "dataset": "nyu-mll/glue",
            "config": "sst2",
            "split": "train",
            "where": '"label" = 0',
            "offset": page * page_size,
            "length": page_size,
        }
    )
    data = response.json()
    if total is None:
        total = data["num_rows_total"]
        print(f"Total rows to fetch: {total}")

    for row in data["rows"]:
        process(row["row"])  # your processing function

    page += 1
    if data["partial"]:
        print("Warning: results are partial (first 5GB only)")
        break
```

### Combined Multi-Column Filter

```python
response = requests.get(
    "https://datasets-server.huggingface.co/filter",
    params={
        "dataset": "nyu-mll/glue",
        "config": "cola",  # CoLA = grammatical acceptability
        "split": "train",
        "where": '"label" = 0 AND "sentence" LIKE \'%the%\'',
        "length": 10,
    }
)
# This finds grammatically unacceptable sentences containing "the"
```

### Float Column Filter

```python
# STSB (Semantic Textual Similarity Benchmark) has float labels 0.0–5.0
response = requests.get(
    "https://datasets-server.huggingface.co/filter",
    params={
        "dataset": "nyu-mll/glue",
        "config": "stsb",
        "split": "train",
        "where": '"label" >= 4.0',
        "length": 10,
    }
)
```

---

## 4. Advanced: Partial Indexing (Large Datasets)

For datasets exceeding **5GB**, the `/filter` endpoint only indexes the first
5GB. This is indicated by `"partial": true` in the response.

### Behavior

- `num_rows_total` reflects only the indexed portion, not the full dataset
- Results are a representative subset (first 5GB of Parquet files)
- The `/size` endpoint shows `estimated_num_rows` — if this is populated, the
  dataset was too large to fully count

### Detection

```python
response = requests.get(
    "https://datasets-server.huggingface.co/filter",
    params={
        "dataset": "bigscience/P3",
        "config": "anli",
        "split": "train",
        "where": '"input" IS NOT NULL',
        "length": 1,
    }
)
data = response.json()
is_partial = data.get("partial", False)
print(f"Results are {'partial' if is_partial else 'complete'}")

# Check dataset size to understand why
size_resp = requests.get(
    "https://datasets-server.huggingface.co/size",
    params={"dataset": "bigscience/P3", "config": "anli"},
)
size_data = size_resp.json()
print(f"Parquet size: {size_data['size']['config']['num_bytes_parquet_files']} bytes")
```

---

## 5. Related Endpoints

### `/statistics` — Descriptive Column Statistics

```
GET /statistics?dataset=nyu-mll/glue&config=sst2&split=train
```

Returns per-column statistics:
- Numeric columns: `min`, `max`, `mean`, `median`, `std`, `nan_count`, `histogram` (10-bin)
- String columns: only `nan_count`
- ClassLabel columns: only `nan_count`

**Use case:** Determine filter ranges before querying (e.g., find the max `idx`).

### `/size` — Dataset Storage Size

```
GET /size?dataset=nyu-mll/glue&config=sst2
```

Returns `num_bytes_original_files`, `num_bytes_parquet_files`, `num_bytes_memory`,
`num_rows`, `num_columns`, `estimated_num_rows` (populated for partial datasets).

**Use case:** Check if a dataset is small enough for full indexing (<5GB parquet).

### `/info` — Dataset Metadata

```
GET /info?dataset=nyu-mll/glue&config=sst2
```

Returns `dataset_info.features` (column schema with dtypes and ClassLabel names),
`splits` (split names, num_examples), and other metadata.

**Use case:** Discover column names, types, and available splits before filtering.

### `/parquet` — Parquet File List

```
GET /parquet?dataset=nyu-mll/glue&config=sst2
```

Returns list of parquet files with `split`, `url`, `size`.

**Use case:** Download Parquet files directly for local DuckDB queries if needed.

### `/rows` — Raw Row Slices

```
GET /rows?dataset=nyu-mll/glue&config=sst2&split=train&offset=0&length=100
```

Returns raw rows without filtering. Uses `offset` and `length` (NOT `limit`).
Does NOT support `WHERE` filtering — use `/filter` for that.

---

## 6. Data Type Handling Details

### Value Types (from `/info` response)

Based on the `/info` endpoint's `dataset_info.features`:

| `_type` | `dtype` | SQL Filter Example | Notes |
|---------|---------|-------------------|-------|
| `Value` | `string` | `"col" = 'text'` | Use single quotes for values |
| `Value` | `int32`, `int64` | `"col" > 100` | Unquoted integers |
| `Value` | `float32`, `float64` | `"col" >= 3.14` | Unquoted floats |
| `Value` | `bool` | `"col" = true` | `true`/`false` (lowercase) |
| `ClassLabel` | — | `"col" = 0` | Use integer index (0-based) |
| `Sequence` | varies | Depends on sub-type | Sequence columns may not support filtering |
| `Image` | — | — | Not filterable directly |
| `Audio` | — | — | Not filterable directly |

### ClassLabel Mapping

ClassLabel stores labels as integers internally. The `names` array in the
features schema maps indices to human-readable names:

```json
{
  "label": {
    "names": ["negative", "positive"],
    "_type": "ClassLabel"
  }
}
```

- `"label" = 0` → "negative"
- `"label" = 1` → "positive"

You CANNOT filter by name (e.g., `"label" = 'positive'` doesn't work).

---

## 7. Limitations & Known Issues

1. **Parquet-only:** Only works on datasets with Parquet exports (most HF datasets
   have them automatically, but some legacy or custom datasets may not)
2. **5GB cap:** Large datasets (>5GB Parquet) return partial results with
   `"partial": true`
3. **No full SQL:** Only `WHERE` clause filtering — no `JOIN`, `GROUP BY`,
   `HAVING`, `SELECT` expressions, or subqueries
4. **100-row max:** `length` parameter caps at 100 rows per request (pagination
   with `offset` required for more)
5. **No COUNT-only:** `num_rows_total` is returned, but there's no dedicated
   count endpoint — you must request at least 1 row to get the count
6. **Unsupported operators:** `IN`, `NOT`, `BETWEEN` return 422 errors
7. **Case sensitivity:** `LIKE` is case-insensitive; `GLOB` is case-sensitive
8. **Rate limiting:** Subject to standard HF API rate limits (same as other
   Datasets Server endpoints)

---

## 8. Comparison: `/filter` vs `/rows` vs `/search`

| Feature | `/rows` | `/filter` | `/search` |
|---------|---------|-----------|-----------|
| Purpose | Raw row access | Condition-based filtering | Full-text search |
| Parameters | `offset`, `length` | `where`, `offset`, `length`, `orderby` | `query`, `offset`, `length` |
| WHERE support | ❌ | ✅ (DuckDB SQL) | ❌ (uses query) |
| ORDER BY | ❌ | ✅ | ❌ |
| Pagination | ✅ (offset) | ✅ (offset) | ✅ (offset) |
| Max rows | 100 | 100 | 100 |
| Partial support | ❌ | ✅ (`partial` flag) | ❌ |
| Best for | Quick data inspection | Precise data extraction | Finding relevant text |

---

## 9. URL Encoding Reference

Since `where` values contain special characters (`"`, `'`, `=`, `<`, `>`, `%`),
proper URL encoding is essential.

### Common encoding table (use `urllib.parse.urlencode()` or equivalent)

| Character | Encoded |
|-----------|---------|
| `"` | `%22` |
| `'` | `%27` |
| `=` | `%3D` |
| `<` | `%3C` |
| `>` | `%3E` |
| `%` | `%25` |
| ` ` | `+` or `%20` |
| `*` | `%2A` |

### Python example (proper encoding)

```python
import urllib.parse, requests

params = {
    "dataset": "nyu-mll/glue",
    "config": "sst2",
    "split": "train",
    "where": '"sentence" LIKE \'%love%\'',
    "offset": 0,
    "length": 5,
}
url = "https://datasets-server.huggingface.co/filter?" + urllib.parse.urlencode(params)
response = requests.get(url)
```

**Always** use a URL encoding library — don't manually construct query strings
with special characters.

---

## Sources

- OpenAPI spec: `https://datasets-server.huggingface.co/openapi.json` (tested 2026-07-25)
- Official docs: `https://huggingface.co/docs/dataset-viewer/en/filter`
- Dataset Viewer docs hub: `https://huggingface.co/docs/dataset-viewer/en/index`
- HF Datasets Server GitHub: `https://github.com/huggingface/datasets-server`
- Live verification: Tested against `/filter`, `/statistics`, `/size`, `/info`, `/parquet`, `/rows` endpoints on GLUE SST2, CoLA, MRPC, STSB datasets
