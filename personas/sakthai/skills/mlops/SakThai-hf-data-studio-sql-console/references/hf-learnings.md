# HF Learnings Log — hf-data-studio-sql-console

## 2026-07-25: hf-data-studio-sql-console-deep-dive — Hugging Face Data Studio & SQL Console Complete Reference

### Summary
Comprehensive deep-dive into Hugging Face's **Data Studio** and its **SQL Console** — the in-browser DuckDB SQL query engine for analyzing Hub datasets at zero cost. Covers the DuckDB WASM architecture, the SQL Console CRUD embeds API, the `hf://` protocol integration with DuckDB CLI, the `hf datasets sql` wrapper, natural language to SQL via HuggingChat integration, leakage detection, column profiling, Storage Bucket querying, and best practices for programmatic dataset analysis without downloading the full dataset.

### Sources
- HF Hub Data Studio docs: https://huggingface.co/docs/hub/en/datasets-viewer
- Dataset viewer analyze guide: https://huggingface.co/docs/dataset-viewer/en/analyze_data
- Dataset viewer DuckDB guide: https://huggingface.co/docs/dataset-viewer/en/duckdb
- `hf datasets sql` CLI docs: https://huggingface.co/docs/hub/en/datasets-viewer#run-sql-queries-on-the-dataset
- Dataset Viewer Quickstart: https://huggingface.co/docs/dataset-viewer/en/quick_start
- DuckDB hf:// docs: https://duckdb.org/docs/extensions/huggingface.html

---

### 1. What is Data Studio?

Data Studio is Hugging Face's **in-browser dataset analysis environment**, accessible from any dataset page on the Hub. It provides:

- **Dataset preview** — browse rows, columns, and splits visually
- **SQL Console** — run DuckDB SQL queries directly in the browser (WASM)
- **Column statistics** — quick histograms, null counts, data types
- **Search & filter** — find specific rows across the dataset
- **Split/subset browser** — navigate multi-config datasets

**Access**: Go to any dataset page → click the **"Data Studio"** tab (or **"Explore"** button for datasets without a viewer).

**URL pattern**: `https://huggingface.co/datasets/<owner>/<dataset>/studio`

---

### 2. SQL Console — Browser-Based DuckDB SQL

The SQL Console is the centerpiece of Data Studio. It runs **DuckDB compiled to WebAssembly (WASM)** entirely in your browser.

#### Architecture

```
Your browser
    │
    ▼
┌─────────────────────────────────┐
│  DuckDB WASM (compiled to JS)   │
│  Runs entirely client-side      │
│  No server calls for query exec │
│  ~8MB wasm binary               │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  Parquet files fetched from HF  │
│  datasets-server /parquet       │
│  HTTP Range requests for pages  │
└─────────────────────────────────┘
```

**Key characteristics**:
- **Zero cost** — queries execute in YOUR browser, NOT on HF servers
- **No data egress** — Parquet data streams directly from HF's CDN
- **SQL dialect** — Full DuckDB SQL (PostgreSQL-compatible)
- **Read-only** — you query, you don't modify the dataset

#### How it Works

1. Data Studio fetches the dataset's Parquet file URLs from `https://datasets-server.huggingface.co/parquet?dataset=<id>`
2. DuckDB WASM creates in-memory tables from the Parquet URLs
3. Your SQL queries run against these tables
4. Results render in the browser as an interactive table

#### Basic Queries

```sql
-- Preview the first 100 rows
SELECT * FROM dataset LIMIT 100;

-- Count total rows
SELECT COUNT(*) FROM dataset;

-- Column statistics
SELECT
  col_name,
  COUNT(*) AS total,
  COUNT(DISTINCT col_name) AS unique_values,
  SUM(CASE WHEN col_name IS NULL THEN 1 ELSE 0 END) AS nulls
FROM dataset;

-- Group by analysis
SELECT label, COUNT(*) AS count, AVG(length) AS avg_len
FROM dataset
GROUP BY label
ORDER BY count DESC;

-- Filtering
SELECT * FROM dataset
WHERE text ILIKE '%error%'
LIMIT 50;
```

---

### 3. `hf datasets sql` CLI — Terminal-Based DuckDB Querying

For programmatic or terminal-based workflows, the `hf` CLI provides a `datasets sql` command:

```bash
# Query a dataset from the terminal
hf datasets sql "SELECT COUNT(*) FROM dataset" --dataset codeparrot/codecomplex

# Specify a split
hf datasets sql "SELECT label, COUNT(*) FROM dataset GROUP BY label" \
  --dataset codeparrot/codecomplex --split train

# Output as JSON
hf datasets sql "SELECT * FROM dataset LIMIT 5" \
  --dataset codeparrot/codecomplex --format json

# Output as CSV
hf datasets sql "SELECT * FROM dataset LIMIT 5" \
  --dataset codeparrot/codecomplex --format csv

# Output as Markdown table
hf datasets sql "SELECT * FROM dataset LIMIT 5" \
  --dataset codeparrot/codecomplex --format markdown
```

**Under the hood**: `hf datasets sql` translates the query into DuckDB SQL and runs it against the dataset's Parquet files on HF's servers. It uses the datasets-server API to discover the Parquet file locations, then streams and queries them.

**Available options**:
| Flag | Description |
|------|-------------|
| `--dataset` | Dataset ID (e.g. `codeparrot/codecomplex`) |
| `--split` | Dataset split (default: infer first available) |
| `--subset` | Dataset subset/config name |
| `--format` | Output format: `table` (default), `json`, `csv`, `markdown` |
| `--where` | Additional WHERE clause filter |

---

### 4. DuckDB `hf://` Protocol — Direct DuckDB Integration

DuckDB natively supports Hugging Face datasets through the `hf://` protocol (available in DuckDB v0.10.3+ via the `huggingface` extension):

```sql
-- Install and load the extension
INSTALL huggingface FROM community;
LOAD huggingface;

-- Query any HF dataset directly
SELECT * FROM 'hf://datasets/codeparrot/codecomplex';
```

**How it works**:
- The `huggingface` DuckDB extension leverages the HF datasets-server API
- It discovers Parquet files for the specified dataset
- Queries run server-side on the Parquet files (pushdown predicates applied)

**Installation of the extension**:
```bash
# DuckDB CLI
duckdb -c "INSTALL huggingface FROM community; LOAD huggingface; SELECT * FROM 'hf://datasets/codeparrot/codecomplex' LIMIT 10;"

# Python
import duckdb
duckdb.sql("INSTALL huggingface FROM community")
duckdb.sql("LOAD huggingface")
result = duckdb.sql("SELECT * FROM 'hf://datasets/codeparrot/codecomplex' LIMIT 10")
print(result)
```

**Supported URI patterns**:
- `hf://datasets/<owner>/<dataset>` — default config and split
- `hf://datasets/<owner>/<dataset>?split=train` — specific split
- `hf://datasets/<owner>/<dataset>?config=<subset>` — specific subset
- `hf://datasets/<owner>/<dataset>?split=test&config=<subset>` — combined

---

### 5. SQL Console Embeds — Saved Queries with CRUD API

Data Studio lets you **save and share queries** as embeds. Each saved query gets a unique URL that embeds the SQL console with your query pre-loaded.

#### Creating an Embed

```bash
# Create a shareable query embed
hf datasets sql "SELECT label, AVG(text_length) FROM dataset GROUP BY label" \
  --dataset codeparrot/codecomplex --create-embed
```

Returns: `https://huggingface.co/datasets/codeparrot/codecomplex/studio?query=<base64-encoded-sql>`

#### Embed CRUD API

The embeds have a CRUD-style API:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/studio?query=<encoded>` | Open SQL Console with pre-loaded query |
| `POST` | `/studio/embeds` | Create a saved embed (requires auth) |
| `GET` | `/studio/embeds/<id>` | View a saved embed |
| `PUT` | `/studio/embeds/<id>` | Update a saved embed |
| `DELETE` | `/studio/embeds/<id>` | Delete a saved embed |

**Share a query link**:
```
https://huggingface.co/datasets/codeparrot/codecomplex/studio?query=SELECT%20label%2C%20COUNT(*)%20FROM%20dataset%20GROUP%20BY%20label
```

**Load a specific row**:
```
https://huggingface.co/datasets/nyu-mll/glue/studio/mrpc/test/241
```

---

### 6. Natural Language to SQL via HuggingChat

Data Studio integrates with HuggingChat for **natural language to SQL**:

1. Open a dataset in Data Studio
2. Click the **"HuggingChat"** icon in the SQL Console toolbar
3. Type your question in natural language (e.g., "Show me the average code length grouped by time complexity")
4. HuggingChat generates the DuckDB SQL for you
5. Click to run the generated SQL

**How it works**: The natural language query is sent to HuggingChat with the dataset schema context (column names, types). HuggingChat generates DuckDB SQL based on the schema. The generated SQL is then run in the SQL Console.

**Zero-cost note**: HuggingChat is free to use. The NL-to-SQL feature does not consume any inference credits — it uses HuggingChat's standard free tier.

---

### 7. Data Leakage Detection (Cross-Split Analysis)

A common ML workflow in Data Studio is **leakage detection** — checking for overlap between train and test splits.

```sql
-- Find rows in test that also appear in train
SELECT t.*
FROM dataset_test t
JOIN dataset_train r ON t.text = r.text
WHERE t.text IS NOT NULL;

-- Count exact duplicates
SELECT COUNT(*)
FROM dataset_test t
JOIN dataset_train r ON t.text = r.text;

-- Find near-duplicates (Levenshtein distance < 5)
-- Note: DuckDB doesn't have built-in Levenshtein without fuzzystrmatch extension
-- Alternative: check common substrings
SELECT t.text, r.text
FROM dataset_test t
JOIN dataset_train r
  ON STRLEN(t.text) = STRLEN(r.text)
  AND t.text != r.text;
```

---

### 8. Column Profiling & Statistics

```sql
-- Full column profile
SELECT
  COUNT(*) AS row_count,
  COUNT(DISTINCT col) AS unique_count,
  COUNT(*) - COUNT(col) AS null_count,
  MIN(col) AS min_val,
  MAX(col) AS max_val,
  AVG(col) AS mean_val,
  MEDIAN(col) AS median_val,
  STDDEV(col) AS std_dev,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY col) AS q1,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY col) AS q3
FROM dataset;

-- Histogram (for numeric columns)
SELECT
  WIDTH_BUCKET(col, min_val, max_val, 20) AS bucket,
  COUNT(*) AS freq
FROM dataset
GROUP BY bucket
ORDER BY bucket;

-- String length distribution
SELECT
  LENGTH(text) AS char_count,
  COUNT(*) AS freq
FROM dataset
GROUP BY char_count
ORDER BY char_count;
```

DuckDB's `histogram()` function provides a quick distribution:

```sql
SELECT histogram(col)
FROM dataset;
```

---

### 9. Storage Bucket Integration

Data Studio also works with **Storage Buckets** (not just datasets):

```sql
-- In DuckDB Python, query a Storage Bucket via HfFileSystem
import duckdb
from huggingface_hub import HfFileSystem

fs = HfFileSystem()
# Mount bucket as virtual filesystem
result = duckdb.sql("""
    SELECT * FROM read_parquet('hf://buckets/username/my-bucket/data/*.parquet')
""")
```

This bridges Data Studio-style analysis to any Parquet data stored in HF Storage Buckets.

---

### 10. From `hf datasets sql` to Python/Pandas

The CLI outputs can be piped directly to data analysis tools:

```bash
# Export to JSON for pandas
hf datasets sql "SELECT * FROM dataset LIMIT 1000" \
  --dataset bigcode/the-stack-dedup --format json > data.json

# Or pipe directly
hf datasets sql "SELECT * FROM dataset LIMIT 1000" \
  --dataset bigcode/the-stack-dedup --format csv | head -5
```

Python-equivalent using `huggingface_hub`:

```python
from huggingface_hub import list_dataset_parquet_files
import duckdb

# Get Parquet file URLs for a dataset
parquet_files = list_dataset_parquet_files("codeparrot/codecomplex")

# Run DuckDB query directly against HF-hosted Parquet
# (DuckDB can read from remote Parquet natively)
first_file = parquet_files[0]
result = duckdb.sql(f"SELECT COUNT(*) FROM '{first_file}'")
print(result.fetchone())
```

---

### 11. Data Studio for Private Datasets

Data Studio works with **private datasets** too — the SQL Console runs in your browser and reads Parquet files through authenticated sessions:

- If you're logged in to HF, the Data Studio tab appears on private datasets
- DuckDB WASM loads Parquet files using your session's auth cookies
- `hf datasets sql` uses your HF token for authentication
- The DuckDB `hf://` extension uses `HF_TOKEN` environment variable

**Note**: The SQL Console **cannot query gated datasets** without proper access permissions.

---

### 12. Integration with Dataset Viewer API

Data Studio is built on top of the Dataset Viewer REST API endpoints:

| Endpoint | Used By SQL Console For |
|----------|------------------------|
| `/parquet?dataset=<id>` | Discovering Parquet file URLs |
| `/first-rows?dataset=<id>` | Initial preview before SQL runs |
| `/info?dataset=<id>` | Schema & column type info |
| `/size?dataset=<id>` | Size estimate for query planning |
| `/statistics?dataset=<id>` | Pre-computed column statistics |
| `/splits?dataset=<id>` | Enumerate available splits/subsets |

---

### 13. Best Practices & Tips

**Performance**:
- Always `LIMIT` your queries during exploration — some datasets are 100M+ rows
- Use `WHERE` clauses with indexed columns (string columns with `==` comparisons)
- Avoid `SELECT *` on wide datasets with many columns
- Prefer aggregation pushdown: `SELECT COUNT(*)` is much faster than loading all rows

**Common pitfalls**:
- DuckDB is **case-insensitive** for keywords but **case-sensitive** for column names
- The `dataset` table name is the default alias — use it unless you define others
- Column names with special characters need double-quoting: `"column-name"`
- The SQL Console is **read-only** — you cannot `INSERT`, `UPDATE`, `DELETE`, or `CREATE TABLE AS`
- Some DuckDB extensions (fuzzy matching, spatial, etc.) are NOT loaded in the WASM build

**Power user tips**:
- Use `DESCRIBE dataset` to see column names and types
- Use `SUMMARIZE dataset` for a quick statistical profile of every column
- Join multiple splits: `SELECT * FROM dataset_train UNION ALL SELECT * FROM dataset_test`
- Window functions work: `SELECT *, ROW_NUMBER() OVER (PARTITION BY label) FROM dataset`
- CTEs work: `WITH filtered AS (SELECT * FROM dataset WHERE label = 'O(n)') SELECT * FROM filtered`

---

### 14. Zero-Cost Summary

| Feature | Cost | Notes |
|---------|------|-------|
| SQL Console (in-browser) | **Free** | Runs in browser WASM, no server compute |
| `hf datasets sql` CLI | **Free** | Query via HF CLI, no credit consumption |
| DuckDB `hf://` extension | **Free** | Direct DuckDB integration, local querying |
| NL-to-SQL via HuggingChat | **Free** | Uses HuggingChat free tier |
| Saved query embeds | **Free** | Shareable query URLs |
| Data leakage detection | **Free** | Just SQL queries in the console |
| Column profiling | **Free** | Built-in DuckDB functions |
| Private dataset queries | **Free** | Uses your existing auth |
| Storage Bucket queries | **Free** | Direct DuckDB read_parquet |

**Beer's practical use**:
- Analyze any HF dataset without downloading GBs of data
- Use `hf datasets sql` for quick scriptable analysis in cron jobs
- Check data leakage between splits before training
- Profile column distributions before fine-tuning
- Query Storage Buckets via DuckDB + HfFileSystem for checkpoint analysis
- All zero-cost, no API calls needed
