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
- ReDoc interactive: https://redocly.github.io/redoc/?url=https://datasets-server.huggingface.co/openapi.json#operation/filterRows
