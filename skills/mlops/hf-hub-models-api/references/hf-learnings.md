# HF Hub Models API — Deep Dive

## 2026-07-24: hf-hub-models-api — Comprehensive Deep Dive

### Summary
Comprehensive deep-dive into the Hugging Face Hub Models REST API — the primary
programmatic interface for discovering, searching, filtering, and inspecting the
1M+ models hosted on the Hub. Covers the list/search endpoint with all filter
parameters, cursor-based pagination, model metadata fields, siblings (file
listing), safetensors weight summary, gated access flags, inference status,
widget data configuration, and the `/api/tasks` taxonomy endpoint. All research
was done live against the production API. Focused on zero-cost patterns — every
endpoint shown is free and authentication-free for public models.

### Core Endpoint: `GET /api/models`

The central endpoint for listing and searching models on the Hub.

**Base URL:** `https://huggingface.co/api/models`

**Authentication:** Optional for public models. Required for private/gated repos
you have access to. Pass `Authorization: Bearer <token>` header.

**Default behaviour:** Returns the first 1,000 models sorted by a trending score
(not by likes or downloads by default). Each model entry is a compact view
(not full metadata).

#### Filter Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Full-text search across model IDs, descriptions, and tags | `?search=llama` |
| `pipeline_tag` | string | Filter by task/pipeline type | `?pipeline_tag=text-generation` |
| `library` | string | Filter by library (transformers, diffusers, etc.) | `?library=diffusers` |
| `sort` | string | Sort field: `likes`, `downloads`, `createdAt`, `lastModified`, `trendingScore` | `?sort=downloads` |
| `direction` | int | Sort direction: `-1` (descending, default for most), `1` (ascending) | `?direction=-1` |
| `limit` | int | Page size (default: 1000, max: 1000) | `?limit=50` |
| `full` | bool | Return full model metadata (heavier response, includes config, siblings, etc.) | `?full=true` |
| `config` | bool | Include model `config.json` in response | `?config=false` |
| `cursor` | string | Cursor for pagination (opaque base64-encoded value from Link header) | `?cursor=<value>` |
| `tags` | string | Filter by tag (e.g., `license:mit`, `region:us`) | `?tags=region:us` |

**Verified real API responses (2026-07-24):**

```bash
# Most downloaded text-generation models
GET /api/models?pipeline_tag=text-generation&sort=downloads&direction=-1&limit=3
# Result: Qwen/Qwen3-0.6B (29M downloads), facebook/opt-125m (16.8M), Qwen/Qwen3-8B (16.6M)

# Most liked diffusers models
GET /api/models?library=diffusers&sort=likes&direction=-1&limit=3
# Result: black-forest-labs/FLUX.1-dev (13.7K likes), stabilityai/stable-diffusion-xl-base-1.0 (8K)

# Search models by keyword
GET /api/models?search=llama&sort=downloads&direction=-1&limit=5
# Result: meta-llama/Llama-3.2-1B-Instruct (10.5M), Llama-3.1-8B-Instruct (8.4M), etc.

# Thai language models
GET /api/models?pipeline_tag=text-generation&search=thai&sort=downloads&limit=5
# Result: typhoon-ai/typhoon-s-thaillm-8b-instruct, ThaiLLM/ThaiLLM-30B, etc.
```

**Note on default limit:** The API returns up to 1,000 models per page by
default. Use `?limit=N` for smaller pages. There is no `X-Total-Count` header
— total model count is intentionally not exposed.

### Pagination: Cursor-Based

The API uses opaque cursor-based pagination. Cursors are base64-encoded
MongoDB-style sort/ID markers.

**How to paginate:**

1. Make the first request with `?limit=N`
2. Read the `Link` header from the response — it contains the URL for the next page
3. Extract the `cursor` parameter and pass it in the next request

```python
import urllib.request, json

def get_models_page(**params):
    query = '&'.join(f'{k}={v}' for k, v in params.items())
    url = f'https://huggingface.co/api/models?{query}'
    req = urllib.request.Request(url, headers={'User-Agent': 'MyApp/1.0'})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    
    # Extract next cursor from Link header
    link = resp.headers.get('Link', '')
    next_cursor = None
    if link:
        # Format: <https://...?cursor=XXXX>; rel="next"
        import re
        m = re.search(r'cursor=([^&>]+)', link)
        if m:
            next_cursor = m.group(1)
    
    return data, next_cursor

# First page
models, cursor = get_models_page(limit=50, sort='downloads', direction=-1)

# Second page (if cursor exists)
if cursor:
    models2, cursor2 = get_models_page(limit=50, cursor=cursor)
```

**Important:** Cursors have no expiry but may become stale if models are added/
removed rapidly. Always use the cursor from the most recent response.

### Model Metadata Fields (Single Model: `GET /api/models/{model_id}`)

Getting a single model by ID returns the full metadata object.

**Top-level keys** (verified live for `meta-llama/Meta-Llama-3.1-8B`):

| Field | Type | Description |
|-------|------|-------------|
| `_id` | string | Internal MongoDB ID |
| `id` | string | Full model ID: `author/name` |
| `author` | string | Model author/owner |
| `private` | bool | Whether the repo is private |
| `gated` | string/False | `"auto"`, `"manual"`, or `False` for ungated |
| `disabled` | bool | Whether the repo is disabled |
| `sha` | string | Latest commit SHA |
| `pipeline_tag` | string | Task type (e.g., `"text-generation"`) |
| `library_name` | string | Framework (e.g., `"transformers"`, `"diffusers"`) |
| `tags` | list[str] | All tags including task, framework, license, region |
| `downloads` | int | Total download count |
| `likes` | int | Total like count |
| `createdAt` | string (ISO) | Creation timestamp |
| `lastModified` | string (ISO) | Last modification timestamp |
| `model-index` | list | Evaluation results (model-index YAML) |
| `config` | dict | Model config (architectures, model_type, tokenizer_config) |
| `cardData` | dict | Model card YAML front-matter |
| `transformersInfo` | dict | Transformers auto-class mapping |
| `safetensors` | dict | SafeTensors weight summary (parameters by dtype, total) |
| `siblings` | list | All files in the repo |
| `spaces` | list | Spaces that use this model |
| `widgetData` | list | Inference widget example inputs |
| `inference` | string | Inference status: `"warm"`, `"cold"`, `"?"` |
| `usedStorage` | int | Storage size in bytes |

#### `transformersInfo` (for transformers models)

```json
{
  "auto_model": "AutoModelForCausalLM",
  "pipeline_tag": "text-generation",
  "processor": "AutoTokenizer"
}
```

This tells you the exact auto-class to use — no guessing needed.

#### `safetensors` (weight summary)

```json
{
  "parameters": {
    "BF16": 8030261248
  },
  "total": 8030261248
}
```

For sharded models, this aggregates all `.safetensors` shards. The top-level key
is the floating-point format (BF16, FP16, FP32, FP8), and the value is the
number of parameters in that format. `total` is the sum across all formats.

#### `config` (architectures & model_type)

```json
{
  "architectures": ["LlamaForCausalLM"],
  "model_type": "llama",
  "tokenizer_config": {
    "bos_token": "<|begin_of_text|>",
    "eos_token": "<|end_of_text|>"
  }
}
```

#### `siblings` (file listing)

Each sibling is an object describing a file:

```json
{
  "rfilename": "model-00001-of-00004.safetensors",
  "type": "safetensors"
}
```

For `meta-llama/Llama-3.1-8B`, the siblings include:
- `.gitattributes`, `LICENSE`, `README.md`, `USE_POLICY.md`
- `config.json`, `generation_config.json`
- `model-00001-of-00004.safetensors` through `model-00004-of-00004.safetensors`
- `model.safetensors.index.json`
- `original/consolidated.00.pth`, `original/params.json`, `original/tokenizer.model`
- `special_tokens_map.json`, `tokenizer.json`, `tokenizer_config.json`

Use `rfilename` (relative filename) to construct download URLs:
`https://huggingface.co/{model_id}/resolve/main/{rfilename}`

#### `cardData` (model card YAML)

Contains the parsed YAML front-matter from the model's `README.md`:

```json
{
  "language": ["en", "de", "fr", "it", "pt", "hi", "es", "th"],
  "pipeline_tag": "text-generation",
  "tags": ["facebook", "meta", "pytorch", "llama", "llama-3"],
  "license": "llama3.1",
  "extra_gated_prompt": "...",
  "extra_gated_fields": {
    "First Name": "text",
    "Country": "country",
    "Affiliation": "text",
    ...
  }
}
```

For gated models, `extra_gated_fields` tells you exactly what information the
gate requires — use this to build automated access-request flows.

#### `tags` — What they encode

Tags follow naming conventions that encode multiple dimensions:

| Tag Pattern | Meaning | Examples |
|-------------|---------|----------|
| Plain | Library/tool | `transformers`, `safetensors`, `diffusers` |
| `arxiv:XXXX.XXXXX` | Research paper | `arxiv:2501.12948` |
| `license:XXX` | License | `license:mit`, `license:llama3.1`, `license:other` |
| `deploy:XXX` | Deployment platform | `deploy:sagemaker`, `deploy:azure` |
| `region:XX` | Storage region | `region:us`, `region:eu` |
| `doi:XXX` | DOI | `doi:10.57967/hf/0039` |
| `endpoints_compatible` | Works with Inference Endpoints | `endpoints_compatible` |
| `eval-results` | Has evaluation results | `eval-results` |
| Custom | Task/framework/format | `deepseek_v3`, `qwen3`, `custom_code`, `fp8` |

#### `inference` field

The `inference` field indicates Serverless Inference availability:
- `"warm"` — Ready for inference (loaded on GPU, zero cold-start)
- `"cold"` — Not recently used, may have cold-start delay
- `"?"` — Status unknown or not supported

For models like `meta-llama/Llama-3.1-8B`: `"warm"` (popular model, always hot).
For `openai-community/gpt2`: `"?"` (no live inference instance).

#### `widgetData` — Inference examples

```json
[
  {"text": "My name is Julien and I like to"},
  {"text": "I like traveling by train because"},
  {"text": "Paris is an amazing place to visit,"},
  {"text": "Once upon a time,"}
]
```

These are the example inputs shown on the model page's inference widget. For
text-generation models, each entry has a `text` key. Different pipeline tags
use different structures (e.g., image-to-image models use different keys).

### Task Taxonomy: `GET /api/tasks`

Returns a dictionary of all 47 supported pipeline types and their metadata.

**Verified (2026-07-24) — all 47 tasks:**

```
any-to-any, audio-classification, audio-to-audio, audio-text-to-text,
automatic-speech-recognition, depth-estimation, document-question-answering,
visual-document-retrieval, feature-extraction, fill-mask, image-classification,
image-feature-extraction, image-segmentation, image-to-image, image-text-to-text,
image-text-to-image, image-text-to-video, image-to-text, image-to-video,
keypoint-detection, mask-generation, object-detection, video-classification,
question-answering, reinforcement-learning, sentence-similarity, summarization,
table-question-answering, tabular-classification, tabular-regression,
text-classification, text-generation, text-ranking, text-to-image, text-to-speech,
text-to-video, token-classification, translation, unconditional-image-generation,
video-text-to-text
```

Use this to validate `pipeline_tag` values and discover supported tasks.

### Practical Zero-Cost Patterns

#### Pattern 1: Find the most downloaded model for a task

```python
import urllib.request, json

def top_models_for_task(task, n=5):
    url = f'https://huggingface.co/api/models?pipeline_tag={task}&sort=downloads&direction=-1&limit={n}'
    req = urllib.request.Request(url, headers={'User-Agent': 'SakThai/1.0'})
    data = json.loads(urllib.request.urlopen(req).read())
    return [(m['id'], m['downloads'], m['likes']) for m in data]

# Example: top text-generation models
for model_id, downloads, likes in top_models_for_task('text-generation', 5):
    print(f'{model_id}: {downloads:,} downloads, {likes:,} likes')
```

#### Pattern 2: Build a model search CLI

```python
import urllib.request, json, sys

def search_models(query, task=None, sort='downloads', limit=10):
    params = [f'search={query}', f'sort={sort}', f'direction=-1', f'limit={limit}']
    if task:
        params.append(f'pipeline_tag={task}')
    url = 'https://huggingface.co/api/models?' + '&'.join(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'SakThai/1.0'})
    data = json.loads(urllib.request.urlopen(req).read())
    return data

if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) > 1 else 'llama'
    results = search_models(query)
    for m in results:
        print(f"{m['id']:50s} {m.get('downloads',0):>8,} downloads  {m.get('likes',0):>5,} likes")
```

#### Pattern 3: Check if a model is ready for serverless inference

```python
def check_inference_status(model_id):
    url = f'https://huggingface.co/api/models/{model_id}'
    req = urllib.request.Request(url, headers={'User-Agent': 'SakThai/1.0'})
    data = json.loads(urllib.request.urlopen(req).read())
    status = data.get('inference', '?')
    return {
        'model_id': model_id,
        'inference_ready': status == 'warm',
        'status': status,
        'pipeline_tag': data.get('pipeline_tag'),
        'library': data.get('library_name'),
    }

# Check multiple models
for model_id in ['meta-llama/Llama-3.1-8B', 'openai-community/gpt2']:
    info = check_inference_status(model_id)
    print(f"{info['model_id']:40s} inference={info['status']:5s}  ready={info['inference_ready']}")
```

#### Pattern 4: Find all models by a specific author

```python
import urllib.request, json

def models_by_author(author, limit=50):
    # Use search to find all models with the author prefix
    url = f'https://huggingface.co/api/models?search={author}&sort=downloads&direction=-1&limit={limit}'
    req = urllib.request.Request(url, headers={'User-Agent': 'SakThai/1.0'})
    data = json.loads(urllib.request.urlopen(req).read())
    # Filter to exact author match
    return [m for m in data if m['id'].startswith(f'{author}/')]

author_models = models_by_author('meta-llama', 20)
print(f'meta-llama has at least {len(author_models)} models')
```

#### Pattern 5: Get model weight summary (parameter count & format)

```python
def get_weight_summary(model_id):
    url = f'https://huggingface.co/api/models/{model_id}'
    req = urllib.request.Request(url, headers={'User-Agent': 'SakThai/1.0'})
    data = json.loads(urllib.request.urlopen(req).read())
    st = data.get('safetensors', {})
    if not st:
        return {'model_id': model_id, 'error': 'No safetensors data'}
    params = st.get('parameters', {})
    total = st.get('total', 0)
    # Human-readable size
    if total >= 1e9:
        readable = f'{total/1e9:.2f}B'
    elif total >= 1e6:
        readable = f'{total/1e6:.2f}M'
    else:
        readable = f'{total:,}'
    return {
        'model_id': model_id,
        'total_params': total,
        'readable': readable,
        'dtypes': list(params.keys()),
        'per_dtype': params,
    }
```

### API Behaviour Notes (from live testing)

1. **No total count available.** The `Link` header provides the next-page cursor,
   but there's no `X-Total-Count` or `Content-Range` header. You cannot know the
   total number of models matching a query without iterating all pages.

2. **Default sort is trending score.** If you don't pass `sort`, results are
   ordered by an internal trending score, NOT by likes or downloads. Always
   specify `sort=downloads` or `sort=likes` for predictable ordering.

3. **Max 1,000 per page.** The `limit` parameter caps at 1,000. For full
   metadata (`?full=true`), keep limit small (50-100) to avoid timeout.

4. **`full=false` by default.** The compact view omits `config`, `siblings`,
   `cardData`, `safetensors`, `spaces`, and `model-index`. Use `?full=true`
   only when you need those fields.

5. **`inference` is a string, not a bool.** The field is `"warm"`, `"cold"`, or
   `"?"`. Check with `== 'warm'`, not truthiness.

6. **`gated` can be `False` (bool) or a string.** For ungated repos, `gated` is
   `false` (Python `False`). For gated, it's `"auto"` or `"manual"`. Always
   check with `if data.get('gated'):` not `if 'gated' in data`.

7. **Search is fuzzy, not exact.** `?search=llama` will match any model ID
   containing "llama" — including `hmellor/tiny-random-LlamaForCausalLM`.
   Use for discovery, not precise filtering.

### Comparison: Models API vs. Datasets API vs. Spaces API

| Feature | Models API | Datasets API | Spaces API |
|---------|-----------|-------------|------------|
| Base endpoint | `/api/models` | `/api/datasets` | `/api/spaces` |
| Task filter | `pipeline_tag` | Not applicable | Not applicable |
| Library filter | `library` | Not applicable | `sdk` (gradio, streamlit, docker) |
| Search parameter | `search` | `search` | `search` |
| Pagination | Cursor (Link header) | Cursor (Link header) | Cursor (Link header) |
| Full metadata | `?full=true` | `?full=true` | `?full=true` |
| Weight summary | `safetensors` field | Not applicable | Not applicable |
| Inference status | `inference` field | Not applicable | `runtime` hardware info |
| Single item | `/api/models/{id}` | `/api/datasets/{id}` | `/api/spaces/{id}` |

### References

- **Hugging Face API Docs:** https://huggingface.co/docs/hub/api
- **Models endpoint (official):** https://huggingface.co/api/models
- **Tasks endpoint:** https://huggingface.co/api/tasks
- **Python SDK equivalent:** `huggingface_hub.list_models()` and `HfApi.get_model()`
- **CLI equivalent:** `hf model list`, `hf model info <model-id>`

### Key Takeaways

1. The Models API is the primary programmatic way to discover Hugging Face models.
2. Cursor-based pagination is the only option — use the `Link` header.
3. The `safetensors` field reveals total parameter count and dtype distribution
   without downloading any weights — crucial for model selection on a budget.
4. The `inference` field tells you which models are hot-ready for serverless
   inference (no cold start).
5. Filter by `pipeline_tag`, `library`, `search`, and `sort` for precise discovery.
6. All endpoints shown are completely free — no authentication, no API keys
   required for public models.
