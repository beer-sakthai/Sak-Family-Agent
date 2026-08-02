# HF Learnings Log — hf-hub-search-discovery-api (Deepened)

## 2026-07-25-v2: Hugging Face Hub Search & Discovery API — Verified API Behavior Deep-Dive (Topic #184, Deepened)

### Summary
Comprehensive deep-dive into the Hugging Face Hub's Search & Discovery API — verified by live endpoint testing on 2026-07-25. Covers all REST API endpoints, field schemas for models/datasets/spaces/collections/papers, sort value mapping, filter tag syntax, pagination via cursor, the `expand`/`full` parameters, `num_parameters` range filtering, rate limiting headers, and edge cases discovered during testing.

**Key insight:** Models, Datasets, and Spaces each return **different field schemas** — no `full=true` equivalent for datasets, no `modelId` in datasets, and Spaces have a unique `/spaces/semantic-search` embedding-based endpoint. Understanding these per-type schema differences is essential for building robust search integrations.

---

### Live-Verified API Endpoints

| Endpoint | Method | Description | Tested |
|----------|--------|-------------|--------|
| `/api/models` | GET | Search & list models | ✅ |
| `/api/datasets` | GET | Search & list datasets | ✅ |
| `/api/spaces` | GET | Search & list Spaces | ✅ |
| `/api/spaces/semantic-search` | GET | Embedding-based Space search | ✅ |
| `/api/collections` | GET | Search collections | ✅ |
| `/api/papers` | GET | Search daily papers | ✅ |

---

### 1. Models API (`/api/models`)

#### Default Response Schema (without `full=true`)

```json
{
  "_id": "6698d8a0653e4babe21e1e7d",
  "id": "meta-llama/Llama-3.1-8B-Instruct",
  "modelId": "meta-llama/Llama-3.1-8B-Instruct",
  "likes": 6392,
  "trendingScore": 26,
  "private": false,
  "downloads": 8247192,
  "tags": ["transformers", "safetensors", "llama", "text-generation", ...],
  "pipeline_tag": "text-generation",
  "library_name": "transformers",
  "createdAt": "2024-07-18T08:56:00.000Z"
}
```

**Fields returned by default (11):** `_id`, `id`, `modelId`, `likes`, `trendingScore`, `private`, `downloads`, `tags`, `pipeline_tag`, `library_name`, `createdAt`

#### With `full=true`

Adds 5 extra fields:
- `author` — HF username (e.g., `"meta-llama"`)
- `gated` — gating status (`false`, `"auto"`, or `true`)
- `lastModified` — ISO datetime string
- `sha` — Git commit hash
- `siblings` — Array of `{rfilename: string}` objects listing all files in the repo (can be 70+ for sharded models)

**Note:** `full` and `expand=siblings` are NOT equivalent — `full=true` is the only way to get `author`, `gated`, `lastModified`, `sha`. The `expand` parameter adds extra metadata to each model object (e.g., `expand=config` returns model config).

#### Query Parameters

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `search` | string | `?search=deepseek` | Full-text search across model IDs and descriptions |
| `filter` | string (repeatable) | `?filter=text-generation&filter=transformers` | Tag filter, AND-combined when multiple |
| `sort` | string | `?sort=trendingScore` | Sort field (camelCase required) |
| `direction` | int | `?direction=-1` | -1=descending (default), 1=ascending |
| `limit` | int | `?limit=50` | Results per page (default: ?) |
| `full` | bool | `?full=true` | Include author/gated/siblings metadata |
| `expand` | string | `?expand=siblings,config` | Add extra fields |
| `num_parameters` | string | `?num_parameters=min:1B,max:8B` | Parameter count range filter |
| `cursor` | string | `?cursor=<base64>` | Cursor-based pagination token |

#### Sort Values (Verified REST API)

| Sort Value | CamelCase | Verified |
|------------|-----------|----------|
| Downloads | `downloads` | ✅ |
| Likes | `likes` | ✅ |
| Created At | `createdAt` | ✅ |
| Last Modified | `lastModified` | ✅ |
| Trending Score | `trendingScore` | ✅ |

**⚠️ Sort values MUST be camelCase.** The REST API rejects snake_case:
- ✅ `sort=trendingScore` works
- ❌ `sort=trending_score` → `"✖ Invalid sort parameter: trending_score"`

#### Filter Tag Syntax

- Simple tags: `filter=text-generation`, `filter=transformers`
- Namespaced tags: `filter=license:mit`, `filter=region:us`, `filter=base_model:meta-llama/Llama-3.1-8B`
- Multiple filters are AND-combined:
  - `?filter=text-generation&filter=transformers&filter=license:mit` → returns models with ALL three tags
- Verified working: triple AND filter (`text-generation + transformers + license:mit`) returned GLM-5.2, Ornith GGUF, DeepSeek-V4-Flash

#### num_parameters Range Filter

- Syntax: `num_parameters=min:<min>,max:<max>`
- Suffixes: `K`, `M`, `B` for kilo/million/billion
- Example: `num_parameters=min:7B,max:9B` — finds models with parameters between 7B and 9B
- Verified: returned `meta-llama/Llama-3.1-8B-Instruct` and `meta-llama/Meta-Llama-3-8B-Instruct`

#### Pagination

The API uses **cursor-based pagination**. There are NO `page` or `offset` parameters.

The pagination cursor is returned in the HTTP `Link` header:
```http
link: <https://huggingface.co/api/models?search=llama&filter=text-generation&limit=1&cursor=<base64>>; rel="next"
```

Usage pattern:
1. Fetch initial results with `limit=N`
2. Parse `Link` header for `rel="next"` URL
3. Use the `cursor` parameter from that URL for the next page
4. Repeat until no `rel="next"` link is present

#### Rate Limiting

Rate limit info is returned in response headers:
```http
ratelimit: "api";r=494;t=104
ratelimit-policy: "fixed window";"api";q=500;w=300
```

- `r` = remaining requests
- `t` = seconds until reset
- `q` = quota per window (500 requests)
- `w` = window duration (300 seconds = 5 minutes)

---

### 2. Datasets API (`/api/datasets`)

#### Response Schema

```json
{
  "_id": "6a00befb7d03878190766021",
  "id": "zake7749/Qwen-3.6-plus-agent-tool-calling-trajectory",
  "author": "zake7749",
  "disabled": false,
  "gated": false,
  "lastModified": "2026-05-10T18:07:53.000Z",
  "likes": 15,
  "private": false,
  "sha": "8a1579e53b85b6845e527e970390ae7e2d02ded8",
  "description": "Multi-turn tool-calling trajectories...",
  "downloads": 804,
  "tags": ["language:en", "format:parquet", "modality:tabular", ...],
  "createdAt": "2026-05-10T17:23:07.000Z",
  "key": ""
}
```

**Key differences from Models API:**
- ❌ No `modelId` field — use `id` for the dataset identifier
- ❌ No `pipeline_tag` or `library_name` fields
- ❌ No `trendingScore` field
- ✅ Has `author`, `disabled`, `description`, `key` fields by default (no `full=true` needed)
- ✅ `description` contains a truncated dataset description (may include HTML)
- `tags` use different format: `language:en`, `size_categories:1K<n<10K`, `format:parquet`, `modality:tabular`

**Query parameters:** Same as Models API (`search`, `filter`, `sort`, `direction`, `limit`)

---

### 3. Spaces API (`/api/spaces`)

#### Response Schema (verified)

```json
{
  "id": "Qwen/Qwen3-TTS",
  "author": "Qwen",
  "sdk": "gradio",
  "likes": 2083,
  "trendingScore": 26,
  "private": false,
  "createdAt": "2026-01-21T09:10:16.000Z",
  "lastModified": "2026-06-09T06:13:30.000Z",
  "ai_category": "Speech Synthesis",
  "ai_short_description": "Generate speech from text using voice design...",
  "featured": true,
  "visibility": "public",
  "runtime": {
    "stage": "RUNNING",
    "hardware": {"current": "zero-a10g", "requested": "zero-a10g"},
    "replicas": {"current": 1, "requested": "auto"}
  },
  "colorFrom": "blue",
  "colorTo": "purple",
  "emoji": "🎙️",
  "pinned": false,
  "tags": ["gradio", "region:us"]
}
```

**Notable fields:**
- `sdk` — Space SDK type (`gradio`, `docker`, `static`)
- `ai_category` — ML task category (e.g., `"Speech Synthesis"`, `"Text Generation"`, `"Chatbots"`)
- `ai_short_description` — AI-generated short description
- `runtime` — Current runtime status including hardware, replicas, domains
- `featured` — Whether the Space is featured
- `trendingScore` — Trending metric

---

### 4. Spaces Semantic Search (`/api/spaces/semantic-search`)

**This is the ONLY embedding-based search endpoint on the Hub.** It's exclusive to Spaces.

```http
GET /api/spaces/semantic-search?q=text+generation&limit=10
```

#### Response

```json
{
  "id": "Qwen/Qwen3-TTS",
  "author": "Qwen",
  "sdk": "gradio",
  "likes": 2083,
  "trendingScore": 26,
  "ai_category": "Speech Synthesis",
  "semanticRelevancyScore": 0.8157105691670071,
  ...
}
```

**Key differences from `/api/spaces`:**
- Uses `q` parameter (NOT `search`) for query
- Returns **`semanticRelevancyScore`** — a float [0,1] indicating embedding similarity
- Single-word queries fall back to full-text search (no semantic scoring)
- Returns 112 results by default (tested with `q=text+generation`)
- Supports `limit` to restrict result count

---

### 5. Collections API (`/api/collections`)

```http
GET /api/collections?search=agent&limit=2
```

#### Response Schema

```json
{
  "slug": "fdtn-ai/antares-6a5804c889e78b51c447c38a",
  "title": "🌟 Antares",
  "description": "Agentic Models for Vulnerability Localization",
  "gating": false,
  "lastUpdated": "2026-07-21T09:51:44.001Z",
  "owner": {
    "name": "fdtn-ai",
    "type": "org",
    "plan": "plus",
    "followerCount": 796
  },
  "items": [
    {
      "position": 0,
      "type": "model",
      "id": "fdtn-ai/antares-1b",
      "repoType": "model",
      "downloads": 5661,
      "likes": 162,
      "pipeline_tag": "text-generation",
      "private": false
    }
  ],
  "theme": "blue",
  "private": false,
  "upvotes": 44
}
```

**Key features:**
- `search` parameter supported for full-text search
- `items` array contains collection entries with `type` (model/space/dataset), full metadata per item
- `owner` includes full user/org profile data
- `upvotes` for community voting
- Items have `position` for ordering within collection

---

### 6. Papers API (`/api/papers`)

```http
GET /api/papers?search=transformer&limit=2
```

#### Response Schema

```json
{
  "id": "2607.21594",
  "title": "Streaming Multi-Agent Autoregressive Diffusion Model...",
  "thumbnailUrl": "https://cdn-thumbnails.huggingface.co/...",
  "upvotes": 11,
  "publishedAt": "2026-07-23T00:00:00.000Z",
  "authors": [
    {"name": "Sicheng Mo", "hidden": false}
  ],
  "summary": "Multi-agent interactive world models...",
  "projectPage": "https://vail-ucla.github.io/worldweaver/"
}
```

**Key features:**
- Uses arXiv IDs (`2607.21594`)
- `search` parameter for full-text
- `authors` array with names
- `summary` is the paper abstract
- `projectPage` links to project website
- `upvotes` for community engagement

---

### 7. Parameter Reference (All Endpoints)

| Parameter | Models | Datasets | Spaces | Semantic | Collections | Papers |
|-----------|--------|----------|--------|----------|-------------|--------|
| `search` | ✅ | ✅ | ✅ | ❌ (uses `q`) | ✅ | ✅ |
| `q` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `filter` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `sort` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `direction` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `limit` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `full` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `expand` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `num_parameters` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `cursor` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

---

### 8. Verified Edge Cases

1. **`full=true` vs `expand=siblings`:**
   - `full=true` adds `author`, `gated`, `lastModified`, `sha`, `siblings`
   - `expand=siblings` adds ONLY `siblings` (and potentially other expand fields)
   - They are NOT equivalent — use `full=true` for the complete profile

2. **`expand=config` returns empty `{}`** for most models — the config is not always available through the search API

3. **Datasets have NO `full=true` equivalent** — `author`, `description`, `disabled`, `sha` are always returned

4. **Datasets use `id` not `modelId`** — always use `result['id']` for dataset identifiers

5. **Spaces semantic search returns `q` fallback:** single-word queries bypass embedding search and use full-text

6. **Rate limiting is per-endpoint** — the `ratelimit` response header shows your current window state

7. **Cursor pagination has no total count** — you cannot determine total result count from the API response alone; iterate until no `rel="next"` Link header

8. **`trendingScore` is missing from dataset responses** — datasets don't have trending score sorting

---

### 9. Practical Usage Patterns

#### Python: Search with pagination
```python
import requests

def search_all_models(search, filter_tags=None, limit=100):
    """Search models with cursor-based pagination."""
    params = {"search": search, "limit": limit}
    if filter_tags:
        params["filter"] = filter_tags  # list or single string

    url = "https://huggingface.co/api/models"
    all_results = []

    while url:
        resp = requests.get(url, params=params if "?" not in url else None)
        params = None  # only send params on first request
        all_results.extend(resp.json())

        # Parse Link header for next cursor
        link = resp.headers.get("Link", "")
        next_url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                next_url = part.split(";")[0].strip("<> ")
        url = next_url

    return all_results
```

#### Python: Semantic space search
```python
import requests

resp = requests.get(
    "https://huggingface.co/api/spaces/semantic-search",
    params={"q": "image generation", "limit": 5}
)
spaces = resp.json()
for space in spaces:
    print(f"{space['id']} (relevance: {space['semanticRelevancyScore']:.3f}) — {space['ai_short_description']}")
```

#### Python: Parameter range filter
```python
import requests

resp = requests.get(
    "https://huggingface.co/api/models",
    params={
        "search": "llama",
        "filter": "text-generation",
        "num_parameters": "min:7B,max:9B",
        "sort": "downloads",
        "direction": -1
    }
)
```

#### cURL: Test filter combinations
```bash
# Triple AND filter
curl -s "https://huggingface.co/api/models?filter=text-generation&filter=transformers&filter=license:mit&sort=trendingScore&limit=3"

# Full metadata
curl -s "https://huggingface.co/api/models?search=qwen&full=true&limit=2"

# Parameter range
curl -s "https://huggingface.co/api/models?search=llama&num_parameters=min:7B,max:9B&limit=3"

# Dataset search
curl -s "https://huggingface.co/api/datasets?search=tool-calling&sort=downloads&limit=3"
```

#### Rate limit awareness
```python
import requests

resp = requests.get("https://huggingface.co/api/models", params={"limit": 1})
rl = resp.headers.get("ratelimit", "")
# Parse: "api";r=494;t=104
remaining, reset_seconds = rl.split(";")[1:3]
remaining = int(remaining.split("=")[1])
reset_seconds = int(reset_seconds.split("=")[1])
if remaining < 10:
    print(f"Approaching rate limit, resets in {reset_seconds}s")
```

---

### 10. What Was Added in This Deepening

| Aspect | Original (27 lines) | Deepened (this version) |
|--------|---------------------|------------------------|
| Endpoints covered | 4 (models, datasets, spaces, collections) | 6 (+ semantic-search, papers) |
| Per-type schema | Brief mention | Full verified field list per type |
| num_parameters | Mentioned | Verified with live test |
| Pagination | Mentioned cursor | Full cursor usage pattern + code |
| Rate limiting | Not mentioned | Headers, parsing, strategy |
| expand/full | Briefly mentioned | Detailed comparison, edge cases |
| Sort values | Listed | Verified all plus error cases |
| Filter syntax | Single filter | Multi-filter AND, namespace tags |
| Code examples | None | Python + cURL patterns |
| Edge cases | None | 8 verified edge cases |
| Comparison table | None | Full endpoint parameter matrix |

---

### Sources
- Live-tested against Hub API at `https://huggingface.co/api/` (2026-07-25)
- Hub docs: https://huggingface.co/docs/hub/en/search
- Hugging Face Hub API: https://huggingface.co/docs/api-hub
- Search Discovery: https://huggingface.co/docs/hub/en/search-discovery

### Tags
`hub-api` `search` `discovery` `models-api` `datasets-api` `spaces-api` `collections` `papers` `pagination` `cursor` `rate-limiting` `semantic-search`
