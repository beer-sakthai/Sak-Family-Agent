---
name: SakThai-hf-hub-search-discovery-api
version: 1.0.0
author: SakThai
license: MIT
category: mlops
---

# Hugging Face Hub Search & Discovery API

Complete reference for searching and discovering resources on the Hugging Face Hub — models, datasets, Spaces, collections, papers, and users.

## REST API Endpoints

| Resource | Endpoint | Python Method |
|----------|----------|---------------|
| Models | `GET /api/models` | `HfApi.list_models()` |
| Datasets | `GET /api/datasets` | `HfApi.list_datasets()` |
| Spaces | `GET /api/spaces` | `HfApi.list_spaces()` |
| Spaces (semantic) | `GET /api/spaces/semantic-search` | `HfApi.search_spaces()` |
| Collections | `GET /api/collections` | `HfApi.list_collections()` |
| Papers | `GET /api/papers` | `HfApi.list_papers()` |
| Daily Papers | `GET /api/daily_papers` | `HfApi.list_daily_papers()` |
| Buckets | `GET /api/buckets` | `HfApi.list_buckets()` |

Base URL: `https://huggingface.co` (or `https://huggingface.co/api`)

## Quick Reference — Python SDK

```python
from huggingface_hub import HfApi
api = HfApi()
```

### Search Models
```python
api.list_models(
    filter=["text-generation", "transformers"],
    search="llama",
    author="meta-llama",
    pipeline_tag="text-generation",
    inference_provider="together",
    num_parameters="min:1B,max:8B",
    sort="downloads",            # or "likes", "trending_score", "last_modified", "created_at"
    limit=20,
    expand=["likes", "downloads", "pipeline_tag"],
    full=False,                  # set True for full metadata
)
```

### Search Datasets
```python
api.list_datasets(
    search="tool calling",
    filter=["task_categories:token-classification"],
    author="bigcode",
    sort="downloads",
    limit=50,
    full=True,
)
```

### Search Spaces
```python
api.list_spaces(
    search="flux",
    sdk="gradio",
    sort="likes",
    limit=20,
)
```

### Semantic Search for Spaces
```python
results = api.search_spaces(
    query="generate image",
    filter="image-generation",
    sdk="gradio",
    include_non_running=False,
)
for r in results:
    print(r.id, r.ai_category, r.likes)
```

### Search Collections
```python
api.list_collections(
    owner="huggingface",
    item="models",
    sort="trending",   # or "lastModified", "upvotes"
    limit=10,
)
```

### Search Papers
```python
api.list_papers(
    query="transformer",
    limit=20,
)

api.list_daily_papers(
    sort="trending",  # or "publishedAt"
    limit=50,
)
```

## Sort Parameter Reference

Python uses **snake_case**, REST API expects **camelCase**:

| Python | REST | Models | Datasets | Spaces | Collections | Papers |
|--------|------|--------|----------|--------|-------------|--------|
| `downloads` | `downloads` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `likes` | `likes` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `last_modified` | `lastModified` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `trending_score` | `trendingScore` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `created_at` | `createdAt` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `trending` | `trending` | ❌ | ❌ | ❌ | ✅ | ✅ |
| `upvotes` | `upvotes` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `publishedAt` | `publishedAt` | ❌ | ❌ | ❌ | ❌ | ✅ |

> **⚠️ Gotcha**: Passing `snake_case` directly to the REST API returns an error. Always use the Python SDK which translates automatically, or use camelCase in raw API calls.

## Filter Tags

Models, Datasets, and Spaces use taxonomy tags for filtering:

**Pipeline tags** (common): `text-generation`, `text-classification`, `image-classification`, `object-detection`, `automatic-speech-recognition`, `text-to-image`, `image-to-text`, `summarization`, `translation`, `fill-mask`, `sentence-similarity`, `token-classification`, `question-answering`, `text2text-generation`, `image-segmentation`, `audio-classification`, `depth-estimation`, `feature-extraction`

**Library prefix**: `library:transformers`, `library:safetensors`, `library:diffusers`, `library:sentence-transformers`, `library:timm`, `library:peft`, `library:accelerate`, `library:onnx`

**Dataset prefix**: `dataset:cot`, `dataset:code`, `dataset:wikipedia`

**License prefix**: `license:mit`, `license:apache-2.0`, `license:cc-by-4.0`, `license:llama2`, `license:openrail`

Multiple filters AND-combine. Pass as list in Python: `filter=["text-generation", "transformers"]`

## Parameter Count Filtering

```python
# Range syntax
num_parameters="min:1B,max:8B"   # 1B to 8B parameters
num_parameters="min:6B"           # 6B and above
num_parameters="max:128B"         # 128B and below
```

Supported suffixes: `K`, `M`, `B`

## Expand (Selective Field Return)

Use `expand` instead of `full=True` to reduce payload:

**Models**: `author`, `baseModels`, `cardData`, `config`, `createdAt`, `downloads`, `evalResults`, `gated`, `gguf`, `inference`, `inferenceProviderMapping`, `lastModified`, `library_name`, `likes`, `pipeline_tag`, `private`, `safetensors`, `sha`, `siblings`, `spaces`, `tags`, `transformersInfo`, `trendingScore`, `widgetData`

**Datasets**: `author`, `cardData`, `citation`, `createdAt`, `description`, `downloads`, `gated`, `lastModified`, `likes`, `private`, `sha`, `siblings`, `tags`, `trendingScore`

**Spaces**: `author`, `cardData`, `createdAt`, `datasets`, `lastModified`, `likes`, `models`, `private`, `runtime`, `sdk`, `sha`, `siblings`, `subdomain`, `tags`, `trendingScore`

> `expand` and `full=True` are mutually exclusive.

## Pagination

All `list_*` methods return generators using `paginate()`. Set `limit` to cap results; `None` fetches all pages.

```python
# Automatic multi-page fetch, capped at 100
for model in api.list_models(sort="downloads", limit=100):
    print(model.modelId)

# Fetch ALL (use carefully with large result sets)
for ds in api.list_datasets(search="code"):
    print(ds.datasetName)
```

## Authentication

- Public resources: no token needed
- Private/gated resources: token required via `token="hf_..."`
- Semantic search: token required for authenticated Spaces

## Key Insights

1. **Semantic search is Spaces-only**: embeddings-based search with automatic full-text fallback for single-word queries. Returns `ai_category` field for categorization.
2. **Sort names differ between Python and REST**: Python's `snake_case` is translated internally. Raw REST calls must use `camelCase`.
3. **`trending_score` needs recent engagement**: returns empty for cold models.
4. **No user search in HfApi**: user search requires raw `GET /api/users?search=...` or web UI.
5. **`full` vs `expand`**: use `expand` for specific fields to reduce API payload size.
6. **Rate limits apply**: see `hf-hub-rate-limits` skill.
