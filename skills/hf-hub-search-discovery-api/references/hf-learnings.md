# HF Learnings Log — hf-hub-search-discovery-api

## 2026-07-25: Hugging Face Hub Search & Discovery API — Complete Deep Dive

### Summary
Comprehensive deep-dive into the Hugging Face Hub's Search & Discovery API. Covers all REST endpoints (`/api/models`, `/api/datasets`, `/api/spaces`, `/api/spaces/semantic-search`, `/api/collections`, `/api/papers`), the `HfApi` Python SDK equivalents, query parameter syntax, filter tag taxonomy, sort value mapping (snake_case → camelCase), pagination via `paginate()`, and expand-based selective field return.

### Key Findings
- **Semantic search is exclusive to Spaces** via `/api/spaces/semantic-search` — uses embedding-based search for multi-word queries, full-text fallback for single-word
- **Sort values differ** between Python SDK (snake_case: `last_modified`) and REST API (camelCase: `lastModified`). Python translates internally
- **REST API rejects raw snake_case sort values** — verified: `sort=trending_score` → `"✖ Invalid sort parameter: trending_score"`
- **`expand` and `full=True` are mutually exclusive** — use expand for selective field return
- **`num_parameters` supports range syntax**: `"min:1B,max:8B"`, suffixes `K`/`M`/`B`
- **Multi-filter AND-combining**: pass multiple `filter` query params or a list in Python

### Verified Sort Values (REST API)
✅ `downloads`, `likes`, `createdAt`, `lastModified`, `trendingScore`
❌ `trending_score`, `trending`, `last_modified`, `created_at`

### Verified API Behaviors
- `GET /api/models` returns list with `modelId` key, supports `search`, `filter`, `sort`, `limit`, `full`, `expand`
- `GET /api/datasets` returns list with `datasetName` key
- `GET /api/spaces/semantic-search` returns list with `id`, `ai_category`, `likes`, `private` keys
- `GET /api/models?filter=text-generation&filter=transformers` AND-combines tags

### Skill
Created `hf-hub-search-discovery-api/` — complete SKILL.md with REST endpoint reference, Python SDK patterns, sort mapping table, filter taxonomy, expand property catalog, and practical search patterns.
