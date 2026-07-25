# HF Learnings Log — Datasets Server: Splits, Rows, Statistics Endpoints

## 2026-07-25: hf-datasets-server-splits-rows-statistics-endpoints — Datasets Server Remaining REST Endpoints (Topic #384)

### Summary
Comprehensive deep-dive into six Datasets Server REST API endpoints that are essential for programmatic dataset exploration but were not yet covered by existing skills: `/splits`, `/first-rows`, `/rows`, `/size`, `/statistics`, and `/is-valid`. Each endpoint was tested against `dair-ai/emotion` with real API responses captured and documented. The `/siblings` endpoint was tested and found non-functional (returns "Not Found"), with an alternative approach using the Hub API recommended.

### Endpoints Covered

| Endpoint | Method | Required Params | Key Response Fields |
|----------|--------|-----------------|-------------------|
| `/splits` | GET | dataset | `splits[].{dataset, config, split}`, `pending`, `failed` |
| `/first-rows` | GET | dataset, config, split | `features[]`, `rows[]`, `truncated_cells` |
| `/rows` | GET | dataset, config, split (+offset, length) | Same as first-rows + `num_rows_total`, `num_rows_per_page` |
| `/size` | GET | dataset (+config) | `size.dataset.{num_bytes_original_files, num_bytes_parquet_files, num_bytes_memory, num_rows}` |
| `/statistics` | GET | dataset, config, split | `num_examples`, `statistics[].{column_name, column_type, column_statistics}` |
| `/is-valid` | GET | dataset | `{preview, viewer, search, filter, statistics}: bool` |

### Key Findings

1. **Splits endpoint** is the entry point for all dataset exploration. For multi-config datasets (e.g., `wikimedia/wikipedia` with 300+ languages), it's essential to enumerate available configs before querying.

2. **First-rows vs Rows**: `/first-rows` returns the first ~100 rows of a split with a fixed offset=0. `/rows` accepts `offset` and `length` params for pagination (max ~100 per page). The `rows` endpoint also returns `num_rows_total` for pagination loops.

3. **Size endpoint** provides memory estimation (`num_bytes_memory`) that is the key metric for deciding whether to load a dataset in-memory vs stream. For `dair-ai/emotion`: original=28MB, parquet=28MB, memory=49MB (Python object overhead adds ~75%).

4. **Statistics endpoint** provides column-type-specific stats: class labels get frequency distributions, string columns get length histograms (10 buckets), numeric columns get min/max/mean/median/std. This enables zero-cost EDA.

5. **is-valid** is a boolean health check — returns `true/false` for preview, viewer, search, filter, and statistics availability. Always check this first before other API calls.

6. **`/siblings` is dead** — Returns "Not Found" as of 2026-07-25. Use the Hub API at `GET https://huggingface.co/api/datasets/{dataset}` instead, which includes a `siblings` array.

### Practical Patterns Documented
- Autonomous dataset discovery: check validity → list splits → get size → preview schema → done
- Class balance check: call statistics endpoint, extract class_label frequencies
- Paginated row access: offset-based generator yielding rows in pages of 100

### Sources
- Real API testing against `https://datasets-server.huggingface.co` (2026-07-25)
- Dataset used for all tests: `dair-ai/emotion` (configs: `split` + `unsplit`)
- Hugging Face Hub API for `/siblings` alternative

### Files Created
- `SKILL.md` (14KB) — full endpoint reference with schemas, real examples, and Python patterns
