# HF Learnings Log

## 2026-07-25: hf-datasets-server-filter-endpoint — Datasets Server `/filter` endpoint with DuckDB SQL WHERE (Topic #330)

### Summary
Complete reference for the Hugging Face Datasets Server `/filter` endpoint, which enables server-side row filtering using DuckDB SQL WHERE clauses without downloading the full dataset. Covers the full API surface (parameters, response format, pagination, ORDER BY), DuckDB SQL dialect supported (operators, column quoting rules, value formatting), column type handling (Value, ClassLabel, Sequence, Image/Audio), partial indexing for large datasets (>5GB), and practical patterns for numeric, string, ClassLabel, and combined filters with code examples. Also covers the four supporting endpoints: `/statistics`, `/size`, `/info`, `/parquet` and how they complement filtering workflows.

### Key Findings
- **Dedicated endpoint:** `/filter` (NOT `/rows`) — `/rows` doesn't support WHERE at all
- **Column quoting:** DuckDB SQL requires double-quoted column names: `"column_name" = value`
- **String quoting:** Single quotes for string values: `"col" = 'text'`
- **ClassLabel:** Filter by integer index (0-based), NOT by name string
- **Supported operators:** `=`, `!=`, `<`, `>`, `<=`, `>=`, `LIKE`, `GLOB`, `IS NULL`, `IS NOT NULL`, `AND`, `OR`
- **NOT supported:** `IN`, `NOT` (keyword prefix), `BETWEEN` — all return 422
- **LIKE vs GLOB:** LIKE is case-insensitive with `%` wildcard; GLOB is case-sensitive with `*` wildcard
- **Partial indexing:** Datasets >5GB Parquet only index first 5GB; `"partial": true` in response
- **Max rows:** 100 per request (pagination via `offset`)
- **ORDER BY:** Supported via `orderby` parameter (e.g., `orderby="idx" DESC`)
- **Related endpoints:** `/statistics` (column stats), `/size` (storage info), `/info` (schema), `/parquet` (file list), `/rows` (unfiltered access), `/search` (full-text)

### Key Code Patterns
```python
# Basic filter
response = requests.get("https://datasets-server.huggingface.co/filter", params={
    "dataset": "nyu-mll/glue",
    "config": "sst2",
    "split": "train",
    "where": '"label" = 1 AND "sentence" LIKE \'%funny%\'',
    "length": 10,
})

# Pagination through results
page = 0
while total is None or page * page_size < total:
    response = requests.get(..., params={..., "offset": page * page_size})
    data = response.json()
    if data.get("partial"): break  # stop if only partial results
    page += 1
```

### Skill Created
`hf-datasets-server-filter-endpoint/` — complete reference with full API spec, DuckDB SQL dialect reference (operator matrix, type handling, encoding), practical patterns (pagination, ORDER BY, multi-column), partial indexing details, related endpoints comparison, and URL encoding guide.

### Sources
- OpenAPI spec: `https://datasets-server.huggingface.co/openapi.json` (verified 2026-07-25)
- Official docs: `https://huggingface.co/docs/dataset-viewer/en/filter`
- Live API tests against GLUE SST2, CoLA, MRPC, STSB datasets via `/filter`, `/statistics`, `/size`, `/info`, `/parquet`, `/rows`
