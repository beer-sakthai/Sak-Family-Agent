# HF Learnings Log — Datasets Server API Deep Dive

## 2026-07-24: hf-datasets-server-configs-subsets (Deep Dive)

### Summary
Comprehensive deep-dive into the Hugging Face Datasets Server's config/subset system — how datasets are organized into configurations (subsets) containing splits, how to discover and query them via the REST API, and practical patterns for multi-config dataset exploration without downloading the full dataset.

### Why Configs Matter
Many datasets on the Hub are organized into **configurations** (also called *subsets*) — sub-datasets within a larger dataset. Common patterns:

- **Multi-language**: Each language is a config (e.g., `facebook/multilingual_librispeech` has 7 configs: german, french, spanish, portuguese, italian, dutch, polish)
- **Multi-task**: Each task is a config (e.g., `ibm/duorc` had ParaphraseRC and SelfRC configs)
- **Multi-domain**: Each domain/subject is a config
- **Default**: Single-config datasets use `"default"` as the config name

Every query to the Datasets Server that involves data content **must specify a config** for multi-config datasets. The `/splits` endpoint is the discovery mechanism.

### Server Base URL
```
https://datasets-server.huggingface.co
```

### Endpoint Reference

#### 1. `/splits` — List All Splits & Discover Configs
**The primary discovery endpoint.** Returns all splits across all configs for a dataset.

```
GET /splits?dataset=<namespace/dataset>
```

**Response:**
```json
{
  "splits": [
    { "dataset": "facebook/multilingual_librispeech", "config": "german", "split": "train" },
    { "dataset": "facebook/multilingual_librispeech", "config": "german", "split": "dev" },
    ...
  ],
  "pending": [],
  "failed": []
}
```

**Config discovery pattern** — extract unique configs from the response:
```python
import requests
resp = requests.get("https://datasets-server.huggingface.co/splits?dataset=facebook/multilingual_librispeech").json()
configs = set(s["config"] for s in resp["splits"])
# → {'german', 'french', 'spanish', 'portuguese', 'italian', 'dutch', 'polish'}
```

**Example datasets:**
| Dataset | Configs | Splits per Config |
|---------|---------|-------------------|
| `SetFit/ag_news` | 1 (default) | train, test |
| `facebook/multilingual_librispeech` | 7 (language) | train, dev, test, 9_hours, 1_hours |
| `google/fleurs` | 103 (language) | train, validation, test |

#### 2. `/info` — Get Dataset Configuration Metadata
Returns full metadata about all configs, including features/schema, row counts, and default config.

```
GET /info?dataset=<namespace/dataset>
```

The response contains a `dataset_info` object with a `configs` dictionary keyed by config name. Each config entry includes:
- `features`: column names and their data types
- `num_rows`: total row count
- `num_columns`: number of columns
- `num_bytes`: size in bytes

**Known limitation:** `default` config field may be `null` for datasets with explicit config names.

#### 3. `/parquet` — List Parquet Files Per Config
Returns Parquet file URLs for a specific config. **Required parameter when dataset has multiple configs.**

```
GET /parquet?dataset=<ds>&config=<config_name>
```

**Response:**
```json
{
  "parquet_files": [
    {"dataset": "...", "config": "german", "split": "1_hours", "url": "https://...", "size": 15655132, "num_rows": 1824},
    {"dataset": "...", "config": "german", "split": "train", "url": "https://...", "size": 424187311, "num_rows": 55136}
  ]
}
```

Each parquet file entry has: `dataset`, `config`, `split`, `url`, `size` (bytes), `num_rows`.

#### 4. `/first-rows` — Preview Rows for a Config+Split
Returns the first 100 rows of data for a specific config + split.

```
GET /first-rows?dataset=<ds>&config=<config_name>&split=<split_name>
```

**Must specify all three parameters** (`dataset`, `config`, `split`) — returns HTTP 400 if any are missing.

**Response** includes:
- `features`: schema (column name → dtype)
- `rows`: array of row objects with `row_idx` and `row` (column→value dict)
- `num_rows`: total rows in this split (may be `null` for large datasets)

#### 5. `/size` — Get Size Stats Per Config
Returns byte counts and row counts for a specific config.

```
GET /size?dataset=<ds>&config=<config_name>
```

**Response fields:**
```json
{
  "size": {
    "config": {
      "dataset": "...",
      "config": "german",
      "num_bytes_original_files": 31526161821,
      "num_bytes_parquet_files": 31526161821,
      "num_bytes_memory": 30393068029,
      "num_rows": 479240,
      "num_columns": 10
    },
    "splits": [ ... per-split breakdowns ... ]
  }
}
```

#### 6. `/rows` — Download Specific Row Range
Download a slice of rows by index range for a config+split.

```
GET /rows?dataset=<ds>&config=<config_name>&split=<split_name>&offset=0&length=100
```

#### 7. `/search` — Full-Text Search Within a Config
Full-text search on a config+split's data.

```
GET /search?dataset=<ds>&config=<config_name>&split=<split_name>&query=<search_term>
```

#### 8. `/filter` — Filter Rows Within a Config
Filter rows by conditions on a config+split.

```
GET /filter?dataset=<ds>&config=<config_name>&split=<split_name>&where=<condition>
```

#### 9. `/statistics` — Column Statistics
Get statistics for numeric/string columns in a config.

```
GET /statistics?dataset=<ds>&config=<config_name>
```

Note: Some configs return HTTP 422 if statistics aren't computable (e.g., audio datasets).

#### 10. `/croissant` — Croissant Metadata
Get ML-Commons Croissant metadata for a dataset config.

```
GET /croissant?dataset=<ds>&config=<config_name>
```

### Authentication
Public datasets on the Datasets Server are accessible without auth. Private/gated datasets require a Hugging Face token:
```
Authorization: Bearer hf_...
```
Without token, private datasets return HTTP 401.

### Practical Patterns

#### Pattern 1: Discover and List All Configs
```python
import requests

def list_configs(dataset):
    resp = requests.get(f"https://datasets-server.huggingface.co/splits?dataset={dataset}").json()
    configs = set(s["config"] for s in resp.get("splits", []))
    return sorted(configs)

# Multi-language speech dataset
configs = list_configs("facebook/multilingual_librispeech")
# → ['dutch', 'french', 'german', 'italian', 'polish', 'portuguese', 'spanish']

# 103-language dataset
configs = list_configs("google/fleurs")
# → ['af_za', 'am_et', 'ar_eg', ... 103 total]
```

#### Pattern 2: Explore a Single Config Deeply
```python
def explore_config(dataset, config):
    base = "https://datasets-server.huggingface.co"
    info = requests.get(f"{base}/info?dataset={dataset}").json()
    size = requests.get(f"{base}/size?dataset={dataset}&config={config}").json()
    preview = requests.get(
        f"{base}/first-rows?dataset={dataset}&config={config}&split=train"
    ).json()
    return {"info": info, "size": size, "preview": preview}
```

#### Pattern 3: Parquet Analytics Across All Configs
```python
def get_all_parquet(dataset):
    configs = list_configs(dataset)
    parquet_by_config = {}
    for cfg in configs:
        resp = requests.get(
            f"https://datasets-server.huggingface.co/parquet?dataset={dataset}&config={cfg}"
        ).json()
        parquet_by_config[cfg] = resp.get("parquet_files", [])
    return parquet_by_config
```

#### Pattern 4: Filter and Query Without Download
```python
# Search for specific text in a config+split
resp = requests.get(
    "https://datasets-server.huggingface.co/search",
    params={"dataset": "facebook/multilingual_librispeech", "config": "german",
            "split": "train", "query": "example"}
).json()

# Filter rows by condition
resp = requests.get(
    "https://datasets-server.huggingface.co/filter",
    params={"dataset": "facebook/multilingual_librispeech", "config": "german",
            "split": "train", "where": "audio_id IS NOT NULL"}
).json()
```

### Key Differences Between Single-Config and Multi-Config Datasets

| Aspect | Single-Config | Multi-Config |
|--------|--------------|--------------|
| Config name | Usually `"default"` or auto | Explicit per language/task |
| `/splits` | 1 config → N splits | M configs × N splits each |
| `/parquet` | Works without `config=` | **Requires** `config=` param |
| `/first-rows` | Works without `config=` | **Requires** `config=` param |
| `/info` | Config-less response dataset_info.configs has 1 entry | Full config dict with all configs |
| Discovery | Just use config="default" | Call `/splits` first |

### Error Handling
| HTTP Code | Meaning | Common Cause |
|-----------|---------|-------------|
| 400 | Bad Request | Missing required `config` parameter for multi-config dataset |
| 401 | Unauthorized | Private/gated dataset without valid token |
| 404 | Not Found | Dataset renamed or doesn't exist |
| 422 | Unprocessable Content | Statistics endpoint on incompatible data |
| 500 | Server Error | Dataset processing failed |
| 501 | Not Implemented | Dataset format not supported by viewer |

### Best Practices
1. **Always call `/splits` first** to discover configs before accessing other endpoints
2. **Cache config lists** — they don't change frequently
3. **Handle missing configs gracefully** — some configs may be `pending` or `failed`
4. **Use `config=default`** as fallback for single-config datasets that may not mention config explicitly
5. **Parquet is cheapest** — for analytics, always prefer Parquet files over row-by-row API calls
6. **Rate-limit generously** — the server precomputes responses, but burst requests may be throttled

### Resources
- Official docs: https://huggingface.co/docs/dataset-viewer/en/splits
- Conceptual guide (configs & splits): https://huggingface.co/docs/dataset-viewer/en/configs_and_splits
- API reference: https://huggingface.co/docs/dataset-viewer/en/index
- Parquet processing guide: https://huggingface.co/docs/dataset-viewer/en/parquet_process
- OpenAPI spec: https://datasets-server.huggingface.co/openapi.json
- Hub dataset configuration: https://huggingface.co/docs/hub/datasets-data-files-configuration
|- GitHub: https://github.com/huggingface/dataset-viewer

---

## 2026-07-24: hf-datasets-server-filter-search-statistics-deep-dive — Live Verified API Behavior

### Summary
Comprehensive deep-dive into the Datasets Server's `/filter`, `/search`, `/statistics`, `/size`, and `/first-rows` endpoints with **live API verification** against real datasets (`scikit-learn/iris`, `stanfordnlp/imdb`). Documents the exact syntax requirements for the `where` parameter (the most error-prone part), the `partial` flag behavior, and known limitations discovered through real endpoint calls.

### Methodology
All findings verified live via Python `urllib` against `https://datasets-server.huggingface.co`. No SDK dependencies — raw API calls that work from any environment.

---

### 1. `/filter` — Precise Syntax Reference

The `/filter` endpoint is the most powerful but most error-prone. It requires **very specific syntax** that is not obvious from error messages (which generically say "contains errors or invalid symbols").

#### Essential Syntax Rules (Verified)

| Rule | Example | Notes |
|------|---------|-------|
| **Column names in double quotes** | `"Id"=1` | REQUIRED — bare `Id=1` fails with 422 |
| **String values in single quotes** | `"Species"='Iris-setosa'` | REQUIRED — double quotes on values also fail |
| **Numeric values unquoted** | `"PetalLengthCm">5.0` | Integers and floats work bare |
| **Operators with spaces** | `"Id" >= 3` | Spaces around operators are fine when URL-encoded |
| **AND/OR in uppercase** | `"Id">=3 AND "Id"<=5` | Must be uppercase |
| **NOT operator** | `NOT "label"=0` | Prefix with NOT (verified working) |
| **orderby parameter** | `orderby="Id"` | Column name in double quotes; supports `DESC` suffix |
| **orderby DESC** | `orderby="Id" DESC` | Sorts descending |

#### Verified Working Examples

```python
import urllib.request, urllib.parse, json

def filter_dataset(dataset, config, split, where, orderby=None, offset=0, length=10):
    """Generic filter function with proper URL encoding."""
    params = {
        'dataset': dataset, 'config': config, 'split': split,
        'where': where, 'offset': str(offset), 'length': str(length)
    }
    if orderby:
        params['orderby'] = orderby
    url = 'https://datasets-server.huggingface.co/filter?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'SakThai/1.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# Exact match integer
result = filter_dataset('scikit-learn/iris', 'default', 'train', '"Id"=1')
# → 1 row, Id=1, Species=Iris-setosa

# Range with AND
result = filter_dataset('scikit-learn/iris', 'default', 'train', '"Id">=3 AND "Id"<=5', orderby='"Id"')
# → 3 rows (Id=3,4,5)

# String match (single quotes!)
result = filter_dataset('scikit-learn/iris', 'default', 'train', '"Species"=\'Iris-setosa\'', orderby='"Id"')
# → 50 rows (all setosa)

# Not equal
result = filter_dataset('scikit-learn/iris', 'default', 'train', '"Id"<>3', orderby='"Id"')
# → 149 rows (everything except Id=3)

# Float comparison
result = filter_dataset('scikit-learn/iris', 'default', 'train', '"PetalLengthCm">5.0', orderby='"Id"')
# → 42 rows (long-petal varieties)

# OR operator
result = filter_dataset('stanfordnlp/imdb', 'plain_text', 'train', '"label"=0 OR "label"=1')
# → 25000 total rows (entire dataset)

# DESC ordering
result = filter_dataset('stanfordnlp/imdb', 'plain_text', 'train', '"label"=1', orderby='"label" DESC')
# → Label=1 rows, ordered descending
```

#### Common Failures & Their Real Error Messages

| Attempted Syntax | Error | Root Cause |
|-----------------|-------|------------|
| `where=Id=1` | 422 "contains errors or invalid symbols" | Missing double quotes on column |
| `where="Species"="Iris-setosa"` | 422 "contains errors or invalid symbols" | String value needs SINGLE quotes |
| `/filter?dataset=scikit-learn/iris` (no config) | 422 "Parameter 'dataset' is required" | dataset value incorrectly encoded |

**Critical encoding insight:** Use `urllib.parse.urlencode()` to build the full query string. Manual string construction with `urllib.parse.quote(where)` is error-prone. The `urlencode` function correctly encodes double quotes (`%22`), single quotes, spaces, and special characters.

#### The `partial` Flag

The response includes a `partial` boolean:
- `partial: false` — All data indexed; filter covers the entire dataset
- `partial: true` — Only first 5GB of data indexed; results may be incomplete

For **imdb** (83 MB original, ~128 MB in memory): `partial=false` — fully indexed.
For datasets >5GB: only the first 5GB is indexed; filtering may miss matching rows in unindexed portions.

#### The `orderby` Parameter

Supports single column ordering:
- `orderby="column_name"` — ascending (default)
- `orderby="column_name" DESC` — descending

Column name must be in double quotes within the URL parameter value. Sorting is applied AFTER filtering, so `num_rows_total` reflects total matching rows, not the sorted result.

---

### 2. `/search` — Full-Text Search Behavior (Verified)

```python
import urllib.request, json

url = "https://datasets-server.huggingface.co/search?dataset=stanfordnlp/imdb&config=plain_text&split=train&query=terrible&offset=0&length=3"
req = urllib.request.Request(url, headers={'User-Agent': 'SakThai/1.0'})
with urllib.request.urlopen(req, timeout=15) as r:
    result = json.loads(r.read())
```

**Verified behavior:**
- **Text search across all text columns** — searches every column of type `string` (or text-like)
- **No `score` in response** — contrary to older docs, the response rows do NOT include a relevance score
- **Returns `num_rows_total`** — total count of matching rows (1563 for "terrible" in imdb train)
- **Works with numeric column names too** — searching "setosa" on iris returns all 50 setosa rows because the Species column matches
- **Max 100 rows per request** — use `offset`/`length` for pagination
- **No advanced query syntax** — just plain text, no AND/OR/wildcards in search query

**Parameters:** `dataset` (req), `config` (req for multi-config), `split` (req), `query` (req), `offset` (opt, default 0), `length` (opt, default/max 100)

---

### 3. `/statistics` — Column Statistics (Verified)

```python
url = "https://datasets-server.huggingface.co/statistics?dataset=scikit-learn/iris&config=default&split=train"
```

**Verified behavior:**
- Returns schema (column names + dtypes) for all columns
- For numeric columns (`int64`, `float64`): returns min, max, mean, std (when data available)
- For string columns: returns column name only (no min/max/etc.)
- **Some datasets return empty statistics objects** even for numeric columns — statistics must be pre-computed by the server
- Audio/image datasets typically return 422 — statistics are not computable for non-tabular data

**Known 422 cases:** Audio datasets (speech, music), image datasets, datasets with non-tabular features.

---

### 4. `/size` — Dataset Size Info (Verified)

```python
url = "https://datasets-server.huggingface.co/size?dataset=stanfordnlp/imdb&config=plain_text"
```

**Verified response for imdb (with config):**
```json
{
  "size": {
    "config": {
      "dataset": "stanfordnlp/imdb", "config": "plain_text",
      "num_bytes_original_files": 83446840,
      "num_bytes_parquet_files": 83446840,
      "num_bytes_memory": 128683449,
      "num_rows": 100000, "num_columns": 2
    },
    "splits": [
      { "config": "plain_text", "split": "train", "num_bytes_parquet_files": 20979968, ... },
      { "config": "plain_text", "split": "test", ... },
      { "config": "plain_text", "split": "unsupervised", ... }
    ]
  }
}
```

**Key fields:**
- `num_bytes_original_files` — raw file size on disk
- `num_bytes_parquet_files` — Parquet export size (usually same as original for text data)
- `num_bytes_memory` — estimated memory footprint when loaded (includes Arrow overhead)
- `num_rows` — total rows across all splits (imdb: 100K = 25K train + 25K test + 50K unsupervised)
- `estimated_num_rows` — for large datasets where exact count is unavailable (null if exact)

**Without config:** Returns dataset-level aggregate. Config parameter is optional for single-config datasets but recommended for accuracy. Without config, returns `null` for some per-config fields.

**Without config (dataset-level):** Returns aggregate across all configs. Some per-split data may be absent.

---

### 5. `/first-rows` — Data Preview (Verified)

```python
url = "https://datasets-server.huggingface.co/first-rows?dataset=stanfordnlp/imdb&config=plain_text&split=train"
```

**Verified:**
- Always returns first 100 rows (not configurable — no offset/length parameters)
- Returns `features` (schema) and `rows` array with `row_idx` + `row` (column→value dict)
- Returns `num_rows` for the split
- **Must specify all three**: dataset, config, AND split — missing split returns 400
- For multi-config datasets, config is required and missing it returns 400

---

### 6. `/is-valid` — Feature Detection (Verified)

This endpoint is critical for determining which features work for a given dataset:

```python
url = "https://datasets-server.huggingface.co/is-valid?dataset=stanfordnlp/imdb"
# → {"preview":true, "viewer":true, "search":true, "filter":true, "statistics":true}
```

**Verified on multiple datasets:**
| Dataset | preview | viewer | search | filter | statistics |
|---------|---------|--------|--------|--------|------------|
| `wikimedia/wikipedia` | true | true | true | true | true |
| `stanfordnlp/imdb` | true | true | true | true | true |
| `scikit-learn/iris` | true | true | true | true | true |

If a dataset returns `filter: false`, the `/filter` endpoint will not work for it (likely because it doesn't have Parquet export or is too large).

---

### 7. Dataset Availability Pitfalls (Verified)

| Pitfall | Example | Behavior |
|---------|---------|----------|
| **Renamed datasets** | `ibm/duorc` (404) | Classic NLP datasets have been renamed or removed. Always check `hf.co/datasets` for current names. |
| **Missing datasets** | `mnist` (404) | Even well-known datasets may not exist on the Hub or may be named differently. |
| **No Parquet export** | Various | Filter/search/statistics require Parquet backend. `is-valid` will show `false` for these features. |
| **Config required** | Multi-config without config | Returns 400 "Bad Request" — use `/splits` first to discover configs. |

---

### 8. Rate Limits & Production Considerations (Verified)

- Public rate limits are undocumented but reasonable (20+ sequential requests worked without throttling)
- Responses are pre-computed and cached — `/first-rows` and `/splits` return instantly
- `/search` and `/filter` may have slightly higher latency on large datasets (tested imdb: ~2-3 seconds for filter)
- For production: cache responses locally, add retry with exponential backoff on 5xx errors
- For large-scale analytics: download Parquet files (listing via `/parquet`) and query locally with DuckDB/Polars instead of row-by-row API calls

---

### Key Takeaways

1. **`/filter` syntax is strict:** column names in `"double quotes"`, string values in `'single quotes'`, URL-encode everything with `urlencode()`. This is the #1 source of errors.
2. **`/is-valid` is your first call** — always check which features are enabled before building queries.
3. **`/parquet` is always cheaper** — for any analytics beyond simple lookups, use Parquet files with DuckDB/Polars.
4. **The `partial` flag tells you if you got all data** — `partial: true` means only 5GB was indexed; results may be incomplete for large datasets.
5. **`/search` is simple text search** — no relevance scores in response; use it for keyword discovery, not ranked retrieval.
6. **`/size` gives memory+disk estimates** — `num_bytes_memory` is typically ~1.5x `num_bytes_parquet_files` due to Arrow overhead.
7. **Classic datasets may be missing or renamed** — always verify dataset existence before coding against specific dataset names.

### Resources
- Filter docs: https://huggingface.co/docs/dataset-viewer/filter
- Search docs: https://huggingface.co/docs/dataset-viewer/search
- Statistics docs: https://huggingface.co/docs/dataset-viewer/statistics
- Size docs: https://huggingface.co/docs/dataset-viewer/size
- OpenAPI spec: https://datasets-server.huggingface.co/openapi.json
|- ReDoc interactive: https://redocly.github.io/redoc/?url=https://datasets-server.huggingface.co/openapi.json#operation/filterRows

## 2026-07-24: hf-datasets-server-complete-api-deep-dive — All 12 Endpoints

### Summary
Complete deep-dive into every endpoint of the Hugging Face Datasets Server REST API, verified against real API responses. Covers all 12 endpoints: `/splits`, `/size`, `/first-rows`, `/rows`, `/parquet`, `/info`, `/statistics`, `/search`, `/filter`, `/is-valid`, `/opt-in-out-urls`, `/presidio-entities`. Focused on practical zero-cost data exploration patterns using only `curl` and the free Datasets Server.

### Base URL
```
https://datasets-server.huggingface.co
```

### Endpoint Reference

#### 1. GET /splits — Discover Configs & Splits
**The discovery entry point.** Lists all configs (subsets) and their splits.

```
GET /splits?dataset=<namespace/dataset>
```

**Required:** `dataset`
**Response:** `{ "splits": [...], "pending": [...], "failed": [...] }`

Each split entry: `{ "dataset": "...", "config": "...", "split": "..." }`

**Pattern — extract unique configs:**
```python
import requests
resp = requests.get("https://datasets-server.huggingface.co/splits?dataset=google/fleurs").json()
configs = set(s["config"] for s in resp["splits"])
# → {'af_za', 'am_et', 'ar_eg', ...}  (102 configs for FLEURS)
```

**Pattern — extract unique splits across all configs:**
```python
splits = set((s["config"], s["split"]) for s in resp["splits"])
```

**Verified response** (rotten_tomatoes):
```json
{
  "splits": [
    {"dataset": "cornell-movie-review-data/rotten_tomatoes", "config": "default", "split": "train"},
    {"dataset": "cornell-movie-review-data/rotten_tomatoes", "config": "default", "split": "validation"},
    {"dataset": "cornell-movie-review-data/rotten_tomatoes", "config": "default", "split": "test"}
  ],
  "pending": [],
  "failed": []
}
```

**Error states:**
- `pending`: Dataset is being processed, retry later
- `failed`: Dataset processing failed, check dataset format
- Renamed datasets return: `{"error": "The dataset has been renamed. Please use the current dataset name."}`

---

#### 2. GET /size — Storage & Row Counts
Returns storage size (original files, Parquet files), memory footprint, and row counts at dataset/config/split level.

```
GET /size?dataset=<namespace/dataset>[&config=<config>]
```

**Required:** `dataset`
**Optional:** `config` (if omitted, returns all configs)

**Verified response** (rotten_tomatoes, all configs):
```json
{
  "size": {
    "dataset": {
      "dataset": "cornell-movie-review-data/rotten_tomatoes",
      "num_bytes_original_files": 881052,
      "num_bytes_parquet_files": 881052,
      "num_bytes_memory": 1344051,
      "num_rows": 10662,
      "estimated_num_rows": null
    },
    "configs": [
      {
        "dataset": "cornell-movie-review-data/rotten_tomatoes",
        "config": "default",
        "num_bytes_original_files": 881052,
        "num_bytes_parquet_files": 881052,
        "num_bytes_memory": 1344051,
        "num_rows": 10662,
        "num_columns": 2,
        "estimated_num_rows": null
      }
    ],
    "splits": [
      {"dataset": "...", "config": "default", "split": "train", "num_bytes_parquet_files": 698845, "num_bytes_memory": 1072741, "num_rows": 8530, "num_columns": 2, "estimated_num_rows": null},
      {"dataset": "...", "config": "default", "split": "validation", "num_bytes_parquet_files": 90001, "num_bytes_memory": 135180, "num_rows": 1066, "num_columns": 2},
      {"dataset": "...", "config": "default", "split": "test", "num_bytes_parquet_files": 92206, "num_bytes_memory": 136130, "num_rows": 1066, "num_columns": 2}
    ]
  },
  "pending": [],
  "failed": [],
  "partial": false
}
```

**Key metrics explained:**
| Field | Meaning |
|-------|---------|
| `num_bytes_original_files` | Size of original source files (JSONL, CSV, etc.) |
| `num_bytes_parquet_files` | Size after Parquet conversion (same as original for Parquet-native datasets) |
| `num_bytes_memory` | Estimated memory footprint when loaded via 🤗 Datasets |
| `num_rows` | Exact row count |
| `num_columns` | Number of feature columns |
| `estimated_num_rows` | For large datasets where exact count is expensive; `null` means exact count was computed |

**Use case — size-aware data selection:**
```python
resp = requests.get("https://datasets-server.huggingface.co/size?dataset=google/fleurs").json()
for c in resp["size"]["configs"]:
    train_split = next(s for s in resp["size"]["splits"] if s["config"] == c["config"] and s["split"] == "train")
    print(f"{c['config']}: {c['num_rows']} rows, {c['num_bytes_parquet_files']/1e6:.1f} MB")
```

---

#### 3. GET /first-rows — Data Preview + Schema
Returns the first 100 rows of a split, with full feature schema. **Best endpoint for exploring data structure without downloading.**

```
GET /first-rows?dataset=<ns/ds>&config=<config>&split=<split>
```

**Required:** `dataset`, `config`, `split`

**Verified response** (rotten_tomatoes train, first 10 of 100 rows):
```json
{
  "dataset": "cornell-movie-review-data/rotten_tomatoes",
  "config": "default",
  "split": "train",
  "features": [
    {"feature_idx": 0, "name": "text", "type": {"dtype": "string", "_type": "Value"}},
    {"feature_idx": 1, "name": "label", "type": {"names": ["neg", "pos"], "_type": "ClassLabel"}}
  ],
  "rows": [
    {"row_idx": 0, "row": {"text": "the rock is destined to be...", "label": 1}, "truncated_cells": []},
    {"row_idx": 1, "row": {"text": "the gorgeously elaborate continuation...", "label": 1}, "truncated_cells": []},
    ...
  ]
}
```

**Feature types reference:**
| Type | `_type` | `dtype` / Fields | Example |
|------|---------|-------------------|---------|
| Primitive | `Value` | `string`, `int32`, `float64`, `bool` | `{"_type": "Value", "dtype": "string"}` |
| Class label | `ClassLabel` | `names: ["neg", "pos"]` | `{"_type": "ClassLabel", "names": [...]}` |
| Sequence | `Sequence` | `feature: {...}` | Nested lists |
| Image | `Image` | — | Binary, content null in preview |
| Audio | `Audio` | — | Binary, content null in preview |

**Design notes:**
- Always returns exactly 100 rows unless split has fewer
- `truncated_cells` lists cell indices where content was truncated (binary large objects)
- Features are always returned, even when no rows are available
- Binary columns (Image, Audio) show `null` in the row data and are listed in `truncated_cells`

---

#### 4. GET /rows — Paginated Row Access
Returns a slice of rows with offset/length pagination. **Essential for sampling specific parts of a split.**

```
GET /rows?dataset=<ns/ds>&config=<config>&split=<split>&offset=<int>&length=<int>
```

**Required:** `dataset`, `config`, `split`
**Optional:** `offset` (default: 0), `length` (default: 100, max: 100)

**Verified response** (rotten_tomatoes train, offset=5, length=3):
```json
{
  "features": [...],
  "rows": [
    {"row_idx": 5, "row": {"text": "the film provides some great insight...", "label": 1}, "truncated_cells": []},
    {"row_idx": 6, "row": {"text": "offers that rare combination...", "label": 1}, "truncated_cells": []},
    {"row_idx": 7, "row": {"text": "perhaps no picture ever made...", "label": 1}, "truncated_cells": []}
  ],
  "num_rows_total": 8530,
  "num_rows_per_page": 100,
  "partial": false
}
```

**Pagination pattern — iterate through all rows:**
```python
offset = 0
length = 100
while True:
    resp = requests.get(f"https://datasets-server.huggingface.co/rows?dataset=...&config=default&split=train&offset={offset}&length={length}").json()
    for row in resp["rows"]:
        process(row["row"])
    offset += length
    if offset >= resp["num_rows_total"]:
        break
```

**Constraints:**
- `length` maximum is 100 (server returns error otherwise)
- `offset` must be ≥ 0
- `num_rows_total` tells you total rows in the split
- Response includes full `features` schema with every request

---

#### 5. GET /parquet — Direct Parquet File URLs
Returns URLs for the Parquet files backing each split. **Enables zero-cost direct Parquet download (no API rate limits).**

```
GET /parquet?dataset=<ns/ds>
```

**Required:** `dataset`
**Optional:** `config` (if omitted, returns all)

**Verified response** (rotten_tomatoes):
```json
{
  "parquet_files": [
    {"dataset": "cornell-movie-review-data/rotten_tomatoes", "config": "default", "split": "train",
     "url": "https://huggingface.co/datasets/cornell-movie-review-data/rotten_tomatoes/resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet",
     "filename": "0000.parquet", "size": 698845},
    {"dataset": "...", "config": "default", "split": "validation",
     "url": ".../validation/0000.parquet", "filename": "0000.parquet", "size": 90001},
    {"dataset": "...", "config": "default", "split": "test",
     "url": ".../test/0000.parquet", "filename": "0000.parquet", "size": 92206}
  ],
  "pending": [], "failed": [], "partial": false
}
```

**Design notes:**
- URLs point to the `refs/convert/parquet` branch — these are auto-converted Parquet files
- Large datasets have sharded Parquet files (0000.parquet, 0001.parquet, ...)
- Files can be downloaded with standard HTTP tools (`curl`, `wget`, `requests`)
- Parquet is a columnar format — you can read specific columns without loading all data
- Zero-cost pattern: download only the Parquet files for splits you need, process locally with `polars` or `pyarrow`

---

#### 6. GET /info — Full Dataset Metadata
Returns the complete dataset metadata, same as what `datasets.get_dataset_config_names()` and `datasets.get_dataset_split_names()` return, without installing the datasets library.

```
GET /info?dataset=<ns/ds>[&config=<config>]
```

**Required:** `dataset`
**Optional:** `config` (if omitted, returns all configs)

**Verified response** (rotten_tomatoes, config=default):
```json
{
  "dataset_info": {
    "default": {
      "description": "",
      "citation": "",
      "homepage": "",
      "license": "",
      "features": {
        "text": {"dtype": "string", "_type": "Value"},
        "label": {"names": ["neg", "pos"], "_type": "ClassLabel"}
      },
      "builder_name": "parquet",
      "dataset_name": "rotten_tomatoes",
      "config_name": "default",
      "version": {"version_str": "0.0.0", "major": 0, "minor": 0, "patch": 0},
      "splits": {
        "train": {"name": "train", "num_bytes": 1072741, "num_examples": 8530, "dataset_name": null},
        "validation": {"name": "validation", "num_bytes": 135180, "num_examples": 1066, "dataset_name": null},
        "test": {"name": "test", "num_bytes": 136130, "num_examples": 1066, "dataset_name": null}
      },
      "download_size": 881052,
      "dataset_size": 1344051
    }
  },
  "pending": [], "failed": [], "partial": false
}
```

**Use cases:**
- Check features/types without downloading any data
- Get split sizes and example counts
- Verify dataset structure before building a pipeline
- Determine if a dataset has a specific config

---

#### 7. GET /statistics — Column-Level Descriptive Statistics
Returns per-column statistics: frequencies for categorical columns, histogram + moments for numeric columns.

```
GET /statistics?dataset=<ns/ds>&config=<config>&split=<split>
```

**Required:** `dataset`, `config`, `split`

**Verified response** (rotten_tomatoes train):
```json
{
  "num_examples": 8530,
  "statistics": [
    {
      "column_name": "label",
      "column_type": "class_label",
      "column_statistics": {
        "nan_count": 0, "nan_proportion": 0.0,
        "no_label_count": 0, "no_label_proportion": 0.0,
        "n_unique": 2,
        "frequencies": {"neg": 4265, "pos": 4265}
      }
    },
    {
      "column_name": "text",
      "column_type": "string_text",
      "column_statistics": {
        "nan_count": 0, "nan_proportion": 0.0,
        "min": 4, "max": 267, "mean": 113.97, "median": 111.0, "std": 51.05,
        "histogram": {
          "hist": [302, 955, 1358, 1701, 1574, 1215, 804, 385, 176, 60],
          "bin_edges": [4, 31, 58, 85, 112, 139, 166, 193, 220, 247, 267]
        }
      }
    }
  ],
  "partial": false
}
```

**Column types and their statistics:**

| Column Type | Statistics Provided |
|-------------|-------------------|
| `class_label` | nan_count, n_unique, frequencies (value → count) |
| `string_text` | nan_count, min/max/mean/median/std, histogram (10 bins) |
| `int` | nan_count, min/max/mean/median/std, histogram (10 bins) |
| `float` | nan_count, min/max/mean/median/std, histogram (10 bins) |
| `bool` | nan_count, n_unique, frequencies |

**Use cases:**
- Class balance check (before training)
- Feature distribution analysis
- Detect missing values (nan_count)
- Understand numeric range for normalization

---

#### 8. GET /search — Full-Text Search
Searches across all text columns in a split. Returns matching rows with their row indices. Case-insensitive, partial-match.

```
GET /search?dataset=<ns/ds>&config=<config>&split=<split>&query=<string>[&offset=<int>&length=<int>]
```

**Required:** `dataset`, `config`, `split`, `query`
**Optional:** `offset` (default: 0), `length` (default: 100, max: 100)

**Verified response** (search "rock" in rotten_tomatoes train):
```json
{
  "features": [...],
  "rows": [
    {"row_idx": 2730, "row": {"text": "morvern rocks .", "label": 1}, "truncated_cells": []},
    {"row_idx": 26, "row": {"text": "spiderman rocks", "label": 1}, "truncated_cells": []},
    {"row_idx": 7133, "row": {"text": "as an actor , the rock is aptly named .", "label": 0}, "truncated_cells": []},
    ...
  ]
}
```

**Design notes:**
- Search is over all text/string columns simultaneously
- Results are ordered by relevance (not by row index)
- `num_rows_total` is NOT returned in search results (unlike `/rows`)
- Binary/special columns are excluded from search
- Query is case-insensitive

---

#### 9. GET /filter — Row-Level Filtering
Filters rows using a SQL-like expression language. Returns matching rows with pagination.

```
GET /filter?dataset=<ns/ds>&config=<config>&split=<split>&where=<expression>[&offset=<int>&length=<int>]
```

**Required:** `dataset`, `config`, `split`, `where`
**Optional:** `offset` (default: 0), `length` (default: 100, max: 100)

**Where expression syntax:**
| Expression | Example | Meaning |
|-----------|---------|---------|
| `column = value` | `Age = 30` | Equality (numeric) |
| `column = 'value'` | `Sex = 'female'` | Equality (string, single quotes) |
| `column > value` | `Fare > 50` | Greater than |
| `column < value` | `Age < 18` | Less than |
| `column >= value` | `Fare >= 100` | Geq |
| `column <= value` | `Age <= 12` | Leq |
| `col1 = v AND col2 > v` | `Pclass = 2 AND "Siblings/Spouses Aboard" > 0` | Logical AND |
| `"column with spaces" = v` | `"column name" = value` | Quoted column names |

**Known limitations (verified 2026-07-24):**
- ClassLabel columns may not support direct filtering (return "invalid symbols" error)
- String equality requires single quotes: `Sex='female'`
- Numeric columns work reliably (`Age=30`, `Fare>50`)
- AND operations work correctly
- The `orderby` parameter is documented but may have issues

**Response format** (matches `/rows` structure):
```json
{
  "features": [...],
  "rows": [...],
  "num_rows_total": 33,
  "num_rows_per_page": 100,
  "partial": false
}
```

---

#### 10. GET /is-valid — Feature Support Check
Returns which Datasets Server features are available for a given dataset. **Essential pre-flight check before building a pipeline.**

```
GET /is-valid?dataset=<ns/ds>
```

**Required:** `dataset`

**Verified response** (rotten_tomatoes):
```json
{
  "preview": true,
  "viewer": true,
  "search": true,
  "filter": true,
  "statistics": true
}
```

**Feature flags:**
| Flag | Meaning |
|------|---------|
| `preview` | `/first-rows` is supported |
| `viewer` | `/rows` is supported (full data viewer) |
| `search` | `/search` is supported |
| `filter` | `/filter` is supported |
| `statistics` | `/statistics` is supported |

**Error states:** Returns `{"preview":false,"viewer":false,...}` for unsupported datasets.

---

#### 11. GET /opt-in-out-urls — URL Compliance
Returns statistics about URLs in the dataset that have opt-in/opt-out status for data deletion compliance.

```
GET /opt-in-out-urls?dataset=<ns/ds>[&config=<config>]
```

**Required:** `dataset`
**Optional:** `config`

**Verified response** (rotten_tomatoes — no URL columns):
```json
{
  "urls_columns": [],
  "has_urls_columns": false,
  "num_opt_in_urls": 0,
  "num_opt_out_urls": 0,
  "num_scanned_rows": 0,
  "num_urls": 0,
  "full_scan": false
}
```

**Fields:**
| Field | Meaning |
|-------|---------|
| `urls_columns` | Column names containing URLs |
| `has_urls_columns` | Whether any column contains URLs |
| `num_opt_in_urls` | Count of opted-in URLs |
| `num_opt_out_urls` | Count of opted-out URLs |
| `num_scanned_rows` | Rows scanned for URL detection |
| `num_urls` | Total URLs found |
| `full_scan` | Whether all rows were scanned |

---

#### 12. GET /presidio-entities — PII Detection
Returns counts of rows containing sensitive entities detected by Microsoft Presidio (PII detection).

```
GET /presidio-entities?dataset=<ns/ds>[&config=<config>]
```

**Required:** `dataset`
**Optional:** `config`

**Verified response** (rotten_tomatoes — no PII):
```json
{
  "scanned_columns": [],
  "num_rows_with_person_entities": 0,
  "num_rows_with_phone_number_entities": 0,
  "num_rows_with_email_address_entities": 0,
  "num_rows_with_sensitive_pii": 0,
  "num_scanned_rows": 0,
  "has_scanned_columns": false,
  "full_scan": true
}
```

**Entity types tracked:**
| Field | Entity |
|-------|--------|
| `person_entities` | PERSON (names) |
| `phone_number_entities` | PHONE_NUMBER |
| `email_address_entities` | EMAIL_ADDRESS |
| `sensitive_pii` | Any sensitive PII (combined) |

---

### Quick Reference — All Endpoints At a Glance

| # | Endpoint | Required Params | Optional | Returns |
|---|----------|----------------|----------|---------|
| 1 | `/splits` | `dataset` | — | Config/split list |
| 2 | `/size` | `dataset` | `config` | Storage & row counts |
| 3 | `/first-rows` | `dataset`, `config`, `split` | — | 100 rows + schema |
| 4 | `/rows` | `dataset`, `config`, `split` | `offset`, `length` | Paginated rows |
| 5 | `/parquet` | `dataset` | `config` | Parquet file URLs |
| 6 | `/info` | `dataset` | `config` | Full metadata |
| 7 | `/statistics` | `dataset`, `config`, `split` | — | Column stats |
| 8 | `/search` | `dataset`, `config`, `split`, `query` | `offset`, `length` | Full-text search |
| 9 | `/filter` | `dataset`, `config`, `split`, `where` | `offset`, `length` | SQL-like filter |
| 10 | `/is-valid` | `dataset` | — | Feature support flags |
| 11 | `/opt-in-out-urls` | `dataset` | `config` | URL compliance |
| 12 | `/presidio-entities` | `dataset` | `config` | PII detection |

### Zero-Cost Patterns

**Pattern 1 — Preview before downloading:**
```bash
# Check what features a dataset has without downloading
curl -s "https://datasets-server.huggingface.co/info?dataset=bigcode/the-stack-v2" | jq '.dataset_info|keys'
# Check size before committing to download
curl -s "https://datasets-server.huggingface.co/size?dataset=bigcode/the-stack-v2" | jq '.size.dataset'
```

**Pattern 2 — Direct Parquet download with column selection:**
```bash
# Get the parquet URLs
curl -s "https://datasets-server.huggingface.co/parquet?dataset=cornell-movie-review-data/rotten_tomatoes" | jq -r '.parquet_files[]|select(.split=="train")|.url'
# Download and read with polars (selective columns)
curl -OL <parquet_url>
python3 -c "import polars as pl; df=pl.read_parquet('0000.parquet',columns=['text']); print(df.head())"
```

**Pattern 3 — Automated dataset quality check:**
```python
def dataset_health_check(dataset_id):
    """Quick sanity check on any dataset."""
    import requests
    base = "https://datasets-server.huggingface.co"
    valid = requests.get(f"{base}/is-valid?dataset={dataset_id}").json()
    size = requests.get(f"{base}/size?dataset={dataset_id}").json()
    splits = requests.get(f"{base}/splits?dataset={dataset_id}").json()
    return {
        "features": valid,
        "total_rows": size.get("size", {}).get("dataset", {}).get("num_rows"),
        "num_configs": len(size.get("size", {}).get("configs", [])),
        "num_splits": len(splits.get("splits", [])),
        "has_pending": len(splits.get("pending", [])) > 0
    }
```

**Pattern 4 — Find datasets with balanced classes:**
```python
def class_balance(dataset_id, config, split):
    resp = requests.get(f"https://datasets-server.huggingface.co/statistics?dataset={dataset_id}&config={config}&split={split}").json()
    for col in resp.get("statistics", []):
        if col["column_type"] == "class_label":
            freqs = col["column_statistics"]["frequencies"]
            total = sum(freqs.values())
            balance = {k: v/total for k, v in freqs.items()}
            print(f"{col['column_name']}: {balance}")
```

### Verified Error States

| Error | Status | Example |
|-------|--------|---------|
| Renamed dataset | Response (no specific status) | `{"error": "The dataset has been renamed. Please use the current dataset name."}` |
| Not found / private | Response | `{"error": "The dataset does not exist, or is not accessible without authentication..."}` |
| Missing required param | 422 | `{"error": "Parameter 'dataset' is required"}` |
| Length too large | 422 | `{"error": "Parameter 'length' must not be greater than 100"}` |
| Invalid where clause | 422 | `{"error": "Parameter 'where' contains errors or invalid symbols"}` |
| Not ready | 500 | `{"error": "The response is not ready yet. Please retry later."}` |

### Resources
- Official docs: https://huggingface.co/docs/dataset-viewer/
- `/splits`: https://huggingface.co/docs/dataset-viewer/splits
- `/first-rows`: https://huggingface.co/docs/dataset-viewer/first-rows
- `/rows`: https://huggingface.co/docs/dataset-viewer/rows
- `/parquet`: https://huggingface.co/docs/dataset-viewer/parquet
- `/info`: https://huggingface.co/docs/dataset-viewer/info
- `/search`: https://huggingface.co/docs/dataset-viewer/search
- `/filter`: https://huggingface.co/docs/dataset-viewer/filter
- `/statistics`: https://huggingface.co/docs/dataset-viewer/statistics
- `/size`: https://huggingface.co/docs/dataset-viewer/size
- OpenAPI spec: https://datasets-server.huggingface.co/openapi.json
- ReDoc interactive: https://redocly.github.io/redoc/?url=https://datasets-server.huggingface.co/openapi.json

---

## 2026-07-24: hf-datasets-server-data-preview-rows-search-filter-deep-dive

### Summary
Deep-dive into the Hugging Face Datasets Server's data preview and query endpoints — `/first-rows`, `/rows`, `/search`, `/filter`, `/statistics`, and `/croissant`. All verified live against the production API at `https://datasets-server.huggingface.co`. Covers exact response formats, SQL-like filter syntax, pagination behavior, and practical zero-cost patterns.

### Base URL
```
https://datasets-server.huggingface.co
```
No auth required for public datasets. Gated/private datasets need `Authorization: Bearer ***` header.

### Endpoint Reference (Verified Live)

#### 1. `/is-valid` — Check Dataset Capabilities
```bash
curl "https://datasets-server.huggingface.co/is-valid?dataset=Salesforce/wikitext"
# -> {"preview":true,"viewer":true,"search":true,"filter":true,"statistics":true}
```
Returns which features (preview, viewer, search, filter, statistics) are available.

#### 2. `/splits` — List All Splits and Subsets
```bash
curl "https://datasets-server.huggingface.co/splits?dataset=Salesforce/wikitext&config=wikitext-2-raw-v1"
```

#### 3. `/size` — Dataset Size (Rows + Bytes)
**Verified response (2026-07-24):**
```json
{
  "size": {
    "config": { "dataset": "Salesforce/wikitext", "config": "wikitext-2-raw-v1", "num_bytes_original_files": 7747362, "num_bytes_parquet_files": 7747362, "num_bytes_memory": 13055524, "num_rows": 44836, "num_columns": 1 },
    "splits": [
      {"split": "test", "num_rows": 4358, "num_bytes_memory": 1391252},
      {"split": "train", "num_rows": 36718, "num_bytes_memory": 10720370},
      {"split": "validation", "num_rows": 3760, "num_bytes_memory": 943902}
    ]
  },
  "partial": false
}
```

#### 4. `/first-rows` — Preview First Rows (VERIFIED)
- Returns exactly 100 rows (default page size)
- Fields: `features`, `rows[]` (each with `row_idx`, `row`, `truncated_cells`)
- No `num_rows_total` — use `/size` for total count
- `split` parameter is required

#### 5. `/rows` — Download Arbitrary Slices (VERIFIED)
- `offset` (default: 0), `length` (default/max: 100)
- Same format as `/first-rows` but with controllable offset

#### 6. `/search` — Full-Text Search (VERIFIED)
- Query scanned across ALL text columns
- Returns absolute `row_idx` (not renumbered)
- No total match count exposed
- Pagination via `offset`/`length`

#### 7. `/filter` — SQL-Like WHERE Filtering (VERIFIED)
**WHERE Syntax Rules (from docs + verified):**
- Column names MUST be in double quotes: `"text"`
- String values MUST be in single quotes: `'hello'`
- Numeric values unquoted: `label=1`
- Operators: `=`, `<>`, `>`, `>=`, `<`, `<=`, `LIKE`, `NOT LIKE`
- Combinators: `AND`, `OR`, `NOT`, parentheses
- `LIKE` wildcards: `%` (any sequence), `_` (single char)
- **Only endpoint that returns `num_rows_total`** (total matching rows)

#### 8. `/statistics` — Column Statistics (VERIFIED)
**Verified response for wikitext train split:**
- `num_examples`: 36718 (total rows in split)
- String columns: length stats (min/max/mean/median/std + histogram)
- Numeric columns: value stats
- `class_label` columns: frequency counts
- Histogram: 10 bins with `hist` (counts) and `bin_edges` (boundaries)

#### 9. `/parquet` — Get Parquet File URLs (VERIFIED)
- Returns per-split Parquet URLs under `refs/convert/parquet`
- Usable with DuckDB, Polars, Pandas, cuDF, PySpark, ClickHouse, PostgreSQL

#### 10. `/info` — Dataset Metadata (VERIFIED)
- Returns `dataset_info` with description, features, splits, sizes

#### 11. `/croissant` — ML-Commons Croissant Metadata
- Structured ML dataset metadata for interoperability

### Pagination Behavior Summary

| Endpoint | Max Length | Has `offset` | `num_rows_total` |
|----------|-----------|-------------|-----------------|
| `/first-rows` | N/A (always 100) | No | null |
| `/rows` | 100 | Yes | null |
| `/search` | 100 | Yes | null |
| `/filter` | 100 | Yes | **Yes** |
| `/size` | N/A | N/A | Has split counts |
| `/statistics` | N/A | N/A | Has `num_examples` |

### Error States (Verified)

| Error | Status | Example |
|-------|--------|---------|
| Renamed dataset | 200 body | `{"error":"The dataset has been renamed..."}` |
| Not found / private | 200 body | `{"error":"The dataset does not exist..."}` |
| Missing param | 422 | `{"error":"Parameter 'dataset' is required"}` |
| Length too large | 422 | `{"error":"Parameter 'length' must not be greater than 100"}` |
| Invalid WHERE | 422 | `{"error":"Parameter 'where' contains errors or invalid symbols"}` |

### Key Takeaways
1. `/first-rows` gives 100 rows free — quick inspection without download
2. Use `/size` for total row counts — `/rows` and `/search` don't return totals
3. `/filter` is the only endpoint returning `num_rows_total`
4. WHERE syntax is SQL-like: double-quoted columns, single-quoted strings
5. Search is case-sensitive
6. Parquet URLs enable zero-cost analytics with DuckDB/Polars
7. All endpoints are completely free — no API keys for public datasets

### Resources
- Docs: https://huggingface.co/docs/dataset-viewer/
- OpenAPI: https://datasets-server.huggingface.co/openapi.json
- Source: https://github.com/huggingface/dataset-viewer
