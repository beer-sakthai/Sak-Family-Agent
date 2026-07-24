# HF Learnings Log — Datasets Server Configs & Subsets

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
- GitHub: https://github.com/huggingface/dataset-viewer
