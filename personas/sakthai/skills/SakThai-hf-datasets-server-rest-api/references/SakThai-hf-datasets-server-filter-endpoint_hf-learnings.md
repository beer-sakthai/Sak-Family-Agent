# HF Learnings — Datasets Server `/filter` Endpoint Source-Level Deep Dive

**Topic:** hf-datasets-server-filter-endpoint (Deep Dive, Topic #61 deepening)
**Date:** 2026-07-25
**Author:** SakThai · Main Lead of the House & Master of Hugging Face
**License:** MIT
**Sources:**
- Source code: `services/search/src/search/routes/filter.py` (277 lines)
- Source code: `libs/libapi/src/libapi/duckdb.py` — index building logic
- Source code: `libs/libcommon/src/libcommon/duckdb_utils.py` — DuckDB utilities, FTS5, BM25
- Official docs: https://huggingface.co/docs/dataset-viewer/en/filter
- OpenAPI spec: https://datasets-server.huggingface.co/openapi.json

---

## 1. Architecture Overview

The `/filter` endpoint is part of the **Datasets Server** — a Python FastAPI service hosted at `datasets-server.huggingface.co`. It uses **DuckDB** as its query engine, running on locally-cached Parquet index files.

### Request Lifecycle

```
Client → GET /filter?dataset=X&config=Y&split=Z&where=...
   │
   ├── 1. Validate parameters (dataset/config/split/where/orderby/offset/length)
   ├── 2. Auth check (optional — public datasets skip)
   ├── 3. Fetch Parquet metadata from cache (MongoDB-backed)
   ├── 4. Build or retrieve DuckDB index file
   │       ├── Check if index exists on disk
   │       ├── If missing: download Parquet files from `refs/convert/parquet` branch
   │       ├── Create DuckDB persistent database with indexed tables
   │       └── Return index file path + partial flag
   ├── 5. Execute filter query via DuckDB SQL
   │       ├── SELECT columns FROM data WHERE {where} ORDER BY {orderby} LIMIT {length} OFFSET {offset}
   │       └── SELECT COUNT(*) FROM data WHERE {where} (for total count)
   ├── 6. Create response (features + rows + metadata)
   └── 7. Return JSON response (cacheable, max_age_long)
```

### Three-Component Architecture

| Component | Technology | Role |
|-----------|-----------|------|
| **Job Queue** | MongoDB + Workers | Processes `/splits`, `/first-rows`, `/parquet` jobs |
| **Cache Layer** | MongoDB | Stores pre-computed responses (parquet metadata, features) |
| **Query Engine** | DuckDB (embedded) | Executes SQL WHERE/ORDER BY on indexed Parquet files |

---

## 2. Source Code Deep Dive (`filter.py`)

### SQL Query Template

```python
FILTER_QUERY = """\
    SELECT {columns}
    FROM data
    {where}
    {orderby}
    LIMIT {limit}
    OFFSET {offset}"""

FILTER_COUNT_QUERY = """\
    SELECT COUNT(*)
    FROM data
    {where}"""
```

Key insight: **Two queries per request** — one for data, one for count. The count query is cheap because DuckDB uses the same index.

### SQL Injection Validation (the Regex Wall)

The `validate_query_parameter()` function applies **strict regex validation** before any SQL is executed:

```python
# Blocked symbols (first line of defense):
SQL_INVALID_SYMBOLS = "|".join([";", "--", r"/\*", r"\*/"])
# → Blocks: semicolons, SQL comments (--, /* */)

# WHERE clause regex pattern (simplified):
SQL_MATCH_WHERE = r"^<EXPR>( <COND> <EXPR>)*$"
# Where EXPR = (col op val) and COND = AND/OR

# ORDER BY regex (single column only):
SQL_MATCH_ORDERBY = r"^<COL>( ASC| DESC)?$"
```

**Effectively allowed syntax:**
- `"column" = value`
- `"column" > 30 AND "name" = 'Simone'` (multiple conditions via AND/OR)
- `"column" LIKE '%pattern%'`
- `"column" IS NULL`, `"column" IS NOT NULL`
- `"column" ASC` / `"column" DESC` (orderby)

**Blocked by regex:**
- `IN`, `NOT`, `BETWEEN` operators
- SQL comments (`--`, `/* */`)
- Subqueries (`SELECT` inside WHERE)
- Multiple statements (semicolons)
- Functions on the left side of operators

### Query Execution in DuckDB

```python
def execute_filter_query(
    index_file_location: str,
    columns: list[str],
    where: str,
    orderby: str,
    limit: int,
    offset: int,
    extensions_directory: Optional[str] = None,
) -> tuple[int, pa.Table]:
    with duckdb_connect(
        database=index_file_location, extensions_directory=extensions_directory, read_only=True
    ) as con:
        filter_query = FILTER_QUERY.format(...)
        filter_count_query = FILTER_COUNT_QUERY.format(...)
        try:
            pa_table = con.sql(filter_query).arrow().read_all()
            num_rows_total = con.sql(filter_count_query).fetchall()[0][0]
        except duckdb.Error as err:
            raise InvalidParameterError(message="A query parameter is invalid") from err
    return num_rows_total, pa_table
```

| Detail | Value |
|--------|-------|
| Connection mode | **Read-only** (immutable index) |
| Output format | **PyArrow Table** (columnar, zero-copy from DuckDB) |
| Error handling | DuckDB errors → 422 `InvalidParameterError` |
| Thread safety | Run via `anyio.to_thread.run_sync()` — runs in a separate thread |

### Index Building Pipeline

When an index doesn't exist, `get_index_file_location_and_build_if_missing()` in `libapi/duckdb.py` does the heavy lifting:

1. **Locate Parquet files** from `refs/convert/parquet` branch for the specific config/split
2. **Cache files locally** via `download_file_from_hub()` — uses `hf_transfer` for speed
3. **Respect 5GB limit** — `get_num_parquet_files_to_process()` truncates to first files within `max_split_size_bytes`
4. **Compute transformed data** — string lengths, audio durations, etc. (for statistics)
5. **Create DuckDB database** — `CREATE TABLE data AS SELECT {columns} FROM read_parquet([files])`
6. **Build full-text search index** (FTS5) — for the `/search` endpoint
7. **Persist to disk** — index file path is returned; subsequent requests skip building

**File naming:**
- Full index: `{dataset}/{config}/{split}.duckdb` → `DUCKDB_DEFAULT_INDEX_FILENAME`
- Partial index (>5GB, first part only): `{dataset}/{config}/{split}.partial.duckdb` → `DUCKDB_DEFAULT_PARTIAL_INDEX_FILENAME`

---

## 3. DuckDB SQL Capabilities (from regex validation)

### Column Name Rules

- **Required:** Double quotes around column names: `"column_name"`
- **Nested/sub-columns:** `"parent"."child"` (dot-separated quoted names)
- **Column names with spaces or special chars:** Always double-quote

### Supported WHERE Operators

| Operator | Matches Regex | Example |
|----------|--------------|---------|
| `=` | ✅ Simple comparison | `"age" = 30` |
| `<>` | ✅ Inequality | `"age" <> 30` |
| `<`, `>`, `<=`, `>=` | ✅ Numeric comparison | `"age" >= 18` |
| `LIKE` | ✅ Case-insensitive pattern | `"name" LIKE '%john%'` |
| `ILIKE` | ✅ Same as LIKE (case-insensitive) | `"name" ILIKE '%john%'` |
| `GLOB` | ✅ Case-sensitive with `*`, `?` | `"name" GLOB 'J*'` |
| `IS NULL` / `IS NOT NULL` | ✅ Null check | `"name" IS NOT NULL` |
| `AND` / `OR` | ✅ Logical combination | `"age" > 30 AND "name" = 'Simone'` |
| `~` / `!~` | ✅ Regex match | `"name" ~ '^J.*'` (DuckDB regex) |
| `SIMILAR TO` | ✅ SQL standard regex | `"name" SIMILAR TO 'J%'` |
| `IN` | ❌ Blocked by regex | Use multiple AND/OR |
| `NOT` | ❌ Blocked by regex | Use `!=` instead |
| `BETWEEN` | ❌ Blocked by regex | `"x" >= 1 AND "x" <= 10` |

### Value Format Rules

| Type | Format | Example |
|------|--------|---------|
| Integer | Unquoted number | `"age" = 30` |
| Float | Unquoted number with decimal | `"price" = 19.99` |
| String | Single-quoted | `"name" = 'Alice'` |
| Bool | `true` / `false` (lowercase) | `"active" = true` |
| Null | `IS NULL` / `IS NOT NULL` | `"col" IS NULL` |
| Escaped quote | `''` (two single quotes) | `"name" = 'O''Brien'` |

### ORDER BY Validation

The ORDER BY validation accepts only a single column expression with optional direction:

```python
SQL_MATCH_ORDERBY = f"^{SQL_MATCH_TRANSFORMED_COL}( {SQL_MATCH_DIRECTION})?$"
# Matches: "col", "col" ASC, "col" DESC
# Does NOT match: multiple columns, expressions, functions
```

---

## 4. Partial Indexing (5GB Limit)

### How It Works

When a dataset split exceeds `max_split_size_bytes` (5GB default):

1. Only the **first N Parquet files** that fit within 5GB are downloaded
2. The DuckDB index is built **only on those files**
3. Response includes `"partial": true`
4. `num_rows_total` reflects only the indexed portion

### Detection Pattern

```python
# From get_num_parquet_files_to_process()
num_parquet_files_to_index, num_bytes, num_rows = get_num_parquet_files_to_process(
    parquet_files=split_parquet_files,
    parquet_metadata_directory=parquet_metadata_directory,
    max_size_bytes=5_000_000_000,  # 5GB
)
```

The `parquet_metadata_directory` stores pre-computed metadata (file sizes, row counts) so the server doesn't need to scan files to determine how many to index.

### Implications

- Results are a **representative subset** (first 5GB of Parquet, not random sampling)
- `num_rows_total` only counts indexed rows, not total dataset rows
- The `/size` endpoint shows `estimated_num_rows` when available
- The filter endpoint returns `partial=true` — consumers should handle this

---

## 5. Caching Strategy

### Two Cache Layers

| Layer | Storage | TTL | Scope |
|-------|---------|-----|-------|
| **MongoDB cache** | Mongo collections | Infinite (until dataset changes) | Parquet metadata, features, split info |
| **DuckDB index files** | Filesystem (`duckdb_index_file_directory`) | Configurable via `expiredTimeIntervalSeconds` | Per-split query indexes |

### Index Cache Lifecycle

1. **Lookup:** Check if `{dataset}/{config}/{split}[.partial].duckdb` exists on disk
2. **Build if missing:** Download Parquet files → create DuckDB database → persist
3. **Read:** Open read-only connection to DuckDB file
4. **Cleanup:** Background cleanup runs with `clean_cache_proba` probability:
   ```python
   if random.random() < clean_cache_proba:  # e.g., 0.01 = 1% of requests
       clean_dir(duckdb_index_file_directory, expiredTimeIntervalSeconds)
   ```

### Cache Invalidation

- **No active invalidation** — indexes are rebuilt when:
  - The index file is missing
  - An OSError during query triggers file removal → next request rebuilds
  - The cleanup routine removes old files (time-based expiry)
- **Revision tracking:** Response headers include `revision` (dataset git SHA)

---

## 6. Authentication

### Endpoint Security Flow

```python
await auth_check(
    dataset=dataset,
    external_auth_url=external_auth_url,
    request=request,
    hf_jwt_public_keys=hf_jwt_public_keys,
    hf_jwt_algorithm=hf_jwt_algorithm,
    hf_timeout_seconds=hf_timeout_seconds,
)
```

| Auth Method | Supported | Notes |
|------------|-----------|-------|
| **Bearer Token** | ✅ | Standard HF API token |
| **JWT** | ✅ | For HF Enterprise Hub |
| **No auth** | ✅ | Public datasets — token optional |

---

## 7. Error Codes & Response Patterns

### 422 Errors (Validation)

| Error | Trigger |
|-------|---------|
| `Parameter 'dataset' is required` | Missing dataset |
| `Parameter 'where' is required` | Missing where clause |
| `Parameter 'offset' must be integer` | Non-integer offset |
| `Parameter 'length' must not be greater than 100` | length > 100 |
| `Parameter 'where' contains invalid symbols` | SQL injection attempt |
| `A query parameter is invalid` | DuckDB SQL execution error |
| `Parameter 'orderby' contains errors or invalid symbols` | Invalid ORDER BY syntax |

### 404 Errors

| Error | Trigger |
|-------|---------|
| Dataset/config/split not found | Non-existent split |
| Dataset not configured | Dataset has no configs |
| Split not found | Invalid split name |

### 500 Errors

| Error | Trigger |
|-------|---------|
| Response not ready | Parquet processing still in progress |
| Dataset error | Underlying dataset has errors (e.g., broken source files) |
| Unexpected error | Internal server error |

---

## 8. Comparison: `/filter` vs `/search` vs `/rows`

| Feature | `/filter` | `/search` | `/rows` |
|---------|-----------|-----------|---------|
| Backend | DuckDB SQL + index | DuckDB FTS5 (full-text search) | Direct row slice |
| Parameters | `where`, `orderby`, `offset`, `length` | `query`, `offset`, `length` | `offset`, `length` |
| WHERE support | ✅ (DuckDB SQL) | ❌ (query-based) | ❌ |
| ORDER BY | ✅ | ❌ | ❌ |
| Full-text search | ❌ | ✅ (BM25 scoring) | ❌ |
| Pagination | ✅ (offset) | ✅ (offset) | ✅ (offset) |
| Max rows | 100 | 100 | 100 |
| Partial support | ✅ (`partial` flag) | ✅ (`partial` flag) | ❌ |
| Index required | ✅ Yes | ✅ Yes (FTS5) | ❌ No (direct file scan) |
| Best for | Precise data extraction | Finding relevant text | Quick data inspection |

### How `/search` Differs Internally

The `/search` endpoint uses DuckDB's **full-text search extension** with:
- **Stemming:** Default "none" (exact match), configurable per dataset
- **Stop words:** 500+ English stop words (a, the, and, etc.)
- **BM25 scoring:** `match_bm25(docname, query_string, fields, k, b, conjunctive)`
- **Tokenization:** `string_split_regex(regexp_replace(lower(strip_accents(s)), '[^a-z]', ' ', 'g'), '\\s+')`

---

## 9. Practical Patterns (Source-Verified)

### Pattern 1: DuckDB SQL Regex (`~` operator)

The `~` operator for regex matching works via DuckDB directly (not blocked by the regex validation):

```python
# Find all rows where sentence matches a regex pattern
response = requests.get(
    "https://datasets-server.huggingface.co/filter",
    params={
        "dataset": "nyu-mll/glue",
        "config": "sst2",
        "split": "train",
        "where": '"sentence" ~ \'.*\\blove\\b.*\'',
        "length": 10,
    }
)
```

**Caution:** The `~` operator is validated by the regex as matching `SQL_MATCH_OP` which includes `~`. This works because the operator regex is permissive (`[~]` is matched by the character class).

### Pattern 2: ORDER BY with nulls

DuckDB defaults to `NULLS LAST` for ASC, `NULLS FIRST` for DESC. No way to override via the `/filter` endpoint (the `NULLS FIRST/LAST` syntax doesn't match the ORDER BY regex).

### Pattern 3: Detecting Partial Results

```python
def check_partial(dataset, config, split):
    resp = requests.get(
        "https://datasets-server.huggingface.co/filter",
        params={
            "dataset": dataset,
            "config": config,
            "split": split,
            "where": '"not_a_real_column" IS NOT NULL',  # dummy filter
            "length": 1,
        }
    )
    return resp.json().get("partial", False)
```

### Pattern 4: Using `/statistics` to Find Filter Ranges

```python
# Before filtering, discover column statistics
stats = requests.get(
    "https://datasets-server.huggingface.co/statistics",
    params={"dataset": "nyu-mll/glue", "config": "sst2", "split": "train"},
).json()

for feature in stats["statistics"]:
    if feature["name"] == "idx":
        print(f"idx range: {feature['min']} to {feature['max']}")
        # → idx range: 0 to 67349
```

### Pattern 5: Max Page Size = 100, Always Paginate

```python
# Full extraction pattern (source-verified)
page = 0
batch_size = 100
all_rows = []

while True:
    resp = requests.get(
        "https://datasets-server.huggingface.co/filter",
        params={
            "dataset": "nyu-mll/glue",
            "config": "sst2",
            "split": "train",
            "where": '"label" = 0',
            "offset": page * batch_size,
            "length": batch_size,
        }
    ).json()
    rows = resp.get("rows", [])
    if not rows:
        break
    all_rows.extend(rows)
    page += 1
    if len(rows) < batch_size:
        break
```

---

## 10. Key Implementation Insights

1. **DuckDB is used in embedded mode** — each split gets its own `.duckdb` database file on disk. This avoids network overhead to a separate database server.

2. **Two queries per request** — `FILTER_QUERY` for data rows, `FILTER_COUNT_QUERY` for total count. The count is always returned, even with `length=0`.

3. **Index files are self-contained** — a single `.duckdb` file holds the full index. No external schema or catalog needed.

4. **Regex validation is the security boundary** — not parameterized SQL. The validation regex blocks SQL injection tokens (`;`, `--`, `/* */`) and limits syntax to simple comparisons. This is a **whitelist approach**, not a blacklist.

5. **Partial indexes are architectural** — the 5GB limit is a hard cap implemented in `get_num_parquet_files_to_process()`. The returned `partial=True` flag lets consumers know they're seeing a subset.

6. **Read-only connections** — DuckDB connections are opened `read_only=True` for safety. The index file is only written during the build step.

7. **Cleanup is probabilistic** — `clean_cache_proba` controls how often old index files are cleaned. Default is low (e.g., 0.01 = 1% of requests trigger cleanup). This avoids cleanup storms under load.

8. **Transformed data** — The `compute_transformed_data()` function creates additional columns like `__string_length_{col}`, `__audio_duration_{col}`, etc. These are joined into the data table via the `CREATE_TABLE_JOIN_WITH_TRANSFORMED_DATA_COMMAND` query, enabling filter queries on string lengths and audio durations even though those aren't native Parquet columns.

9. **The filter endpoint powers the Hub dataset viewer UI** — when you type a WHERE clause in the "Filter rows" tab of a dataset page, it calls this exact endpoint.

10. **No `IN` or `BETWEEN` support** — These DuckDB-native operators are blocked by the regex validation. For `IN` replacements, use multiple `OR` conditions. For `BETWEEN`, use `AND`.

---

## Skill Created

`hf-datasets-server-filter-endpoint/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with source-level implementation deep dive.
