# HF Inference Client — Embeddings Patterns (Serverless & Free)

> *Entry 380 in cumulative HF learnings*
> *Topic: `hf-inference-client-embeddings-patterns`*
> *Date: 2026-07-25*
> *Sources: `huggingface_hub` source code (`InferenceClient`), HF REST API (`/api/tasks`), `_providers/hf_inference.py`*

---

## 1. Architecture: How Embeddings Flow Through the Client

```
InferenceClient.feature_extraction(text)
    │
    ├─ model_id = model or self.model (default: None → recommended by /api/tasks)
    ├─ provider = "auto" (default) → resolves to "hf-inference"
    ├─ get_provider_helper("hf-inference", "feature-extraction", model_id)
    │   └─ Returns HFInferenceFeatureExtractionTask instance
    ├─ prepare_request(inputs, parameters, headers, model, api_key)
    │   └─ Payload: {"inputs": text, "normalize": ..., "prompt_name": ...}
    ├─ POST to https://api-inference.huggingface.co/models/{model_id}/pipeline/feature-extraction
    │   [NOTE: special /pipeline/{task} suffix — unique to feature-extraction and sentence-similarity]
    └─ Returns np.ndarray(dtype=float32)
```

### Key difference from other tasks
`feature-extraction` and `sentence-similarity` use a **different URL pattern** than all other inference tasks:

- Most tasks: `POST /models/{model_id}`
- Embeddings: `POST /models/{model_id}/pipeline/feature-extraction`
- Similarity:  `POST /models/{model_id}/pipeline/sentence-similarity`

This is because embedding models often support **multiple tasks** (e.g., `sentence-transformers/all-MiniLM-L6-v2` can do both feature-extraction and sentence-similarity). The `/pipeline/` suffix disambiguates which endpoint to hit.

Source: `HFInferenceTask._prepare_url()` in `_providers/hf_inference.py`:
```python
return (
    f"{self.base_url}/models/{mapped_model}/pipeline/{self.task}"
    if self.task in ("feature-extraction", "sentence-similarity")
    else f"{self.base_url}/models/{mapped_model}"
)
```

---

## 2. Provider Support for Embeddings

| Provider | Feature Extraction | Sentence Similarity | Notes |
|----------|:---:|:---:|-------|
| `hf-inference` | ✅ | ✅ | Free tier, default. Uses HF Inference API. |
| `scaleway` | ✅ | ❌ | Requires paid Scaleway account |
| `together` | ✅ | ❌ | Requires paid Together AI account |
| All others | ❌ | ❌ | No embeddings support |

**`hf-inference` is the only provider offering free embeddings** — all others require billing.

Source: `PROVIDERS` dict in `huggingface_hub/inference/_providers/__init__.py`

---

## 3. Default/Widely Available Models

### Default recommended models (from `/api/tasks`):
| Task | Default Model | Notes |
|------|--------------|-------|
| `feature-extraction` | `facebook/bart-base` | Encoder-decoder; 768-dim hidden |
| `sentence-similarity` | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim, good for similarity |

### Top embedding models on Hub (by downloads):
| Model | Dimensions | Language | Library | Downloads |
|-------|:----------:|:--------:|:--------:|:---------:|
| `BAAI/bge-small-en-v1.5` | 384 | English | sentence-transformers | 67.7M |
| `BAAI/bge-large-en-v1.5` | 1024 | English | sentence-transformers | 13.6M |
| `intfloat/multilingual-e5-large` | 1024 | Multilingual | sentence-transformers | 11.6M |
| `Qwen/Qwen3-Embedding-0.6B` | 1792 | Multilingual | custom | 10.8M |
| `BAAI/bge-base-en-v1.5` | 768 | English | sentence-transformers | 8.5M |
| `mixedbread-ai/mxbai-embed-large-v1` | 1024 | English | sentence-transformers | 4.9M |
| `jinaai/jina-embeddings-v3` | 1024 | Multilingual | custom | 3.2M |
| `Qwen/Qwen3-Embedding-8B` | 4096 | Multilingual | custom | 3.2M |

### Recommended for zero-cost:
1. **`BAAI/bge-small-en-v1.5`** — Best quality/speed trade-off (384-dim, fast, widely available)
2. **`sentence-transformers/all-MiniLM-L6-v2`** — Default for sentence-similarity, reliable (384-dim)
3. **`BAAI/bge-base-en-v1.5`** — Higher quality but slower (768-dim)
4. **`Qwen/Qwen3-Embedding-0.6B`** — Newer, multilingual, 1792-dim (larger but richer)

---

## 4. Method Signatures & Parameters

### `feature_extraction()`
```python
def feature_extraction(
    self,
    text: str | list[str],         # Single string or batch
    *,
    normalize: bool | None = None,        # L2-normalize output (TEI only)
    prompt_name: str | None = None,       # Sentence-transformers prompt key
    truncate: bool | None = None,         # Truncate to model's max length (TEI only)
    truncation_direction: Literal["left", "right"] | None = None,
    dimensions: int | None = None,        # Output dims (OpenAI-compatible only)
    encoding_format: Literal["float", "base64"] | None = None,  # Output format (OpenAI-compatible only)
    model: str | None = None,             # Model ID or endpoint URL
) -> np.ndarray                           # Always float32
```

### `sentence_similarity()`
```python
def sentence_similarity(
    self,
    sentence: str,                         # Source sentence
    other_sentences: list[str],            # Comparative sentences
    *,
    model: str | None = None,              # Model ID or endpoint URL
) -> list[float]                           # Similarity scores [0,1]
```

### Parameter availability by provider:

| Parameter | hf-inference | TEI (Endpoint) | OpenAI-compat |
|-----------|:------------:|:--------------:|:-------------:|
| `normalize` | ❌ (ignored) | ✅ | ❌ |
| `prompt_name` | ✅ (ST models) | ✅ (ST models) | ❌ |
| `truncate` | ❌ (ignored) | ✅ | ❌ |
| `truncation_direction` | ❌ (ignored) | ✅ | ❌ |
| `dimensions` | ❌ | ❌ | ✅ |
| `encoding_format` | ❌ | ❌ | ✅ |

**Important:** `normalize`, `truncate`, and `truncation_direction` are only supported when the underlying server runs **Text-Embeddings-Inference (TEI)**. The serverless `hf-inference` provider ignores these silently.

**`normalize=True`** is crucial if you plan to compute cosine similarity client-side. Without normalization, cosine similarity can produce inconsistent results.

---

## 5. Provider Routing Details

### Auto-routing flow
```python
client = InferenceClient(provider="auto")
client.feature_extraction("text", model="BAAI/bge-small-en-v1.5")
```

1. `provider="auto"` triggers `_fetch_inference_provider_mapping(model)`
2. This calls `GET https://huggingface.co/api/models/BAAI/bge-small-en-v1.5/inference-providers`
3. Returns ordered list of providers (by user's settings on `hf.co/settings/inference-providers`)
4. First `live` provider with the requested task is selected
5. If the user hasn't configured provider order, defaults to `hf-inference`

### Explicit hf-inference:
```python
client = InferenceClient(provider="hf-inference")
# Bypasses auto-routing, always uses HF Inference API
```

### Using a TEI endpoint directly:
```python
client = InferenceClient(model="https://your-tei-endpoint.com")
# If model starts with http:// or https://, always uses hf-inference provider
# (which handles arbitrary URLs as Inference Endpoints)
```

---

## 6. Embedding Pooling: Per-Token vs Sentence-Level

**Critical:** Most sentence-transformer models return **per-token** embeddings, not a single sentence embedding!

### What `feature_extraction` returns:
- **BERT-style models** (e.g., `facebook/bart-base`): `(batch_size, sequence_length, hidden_dim)` — one vector per token
- **Sentence-transformers** with pooling layer: Depends on model config
- **Some models** (e.g., `BAAI/bge-*`) include a pooling instruction in the config

### How to get a single sentence embedding:
**Option 1: Use `sentence_similarity`** — handles pooling server-side
```python
scores = client.sentence_similarity("query", ["doc1", "doc2", "doc3"])
```

**Option 2: Manual mean-pooling** (for feature_extraction output)
```python
import numpy as np
emb = client.feature_extraction("My sentence")  # (tokens, 768)
sentence_embedding = emb.mean(axis=0)           # (768,)
```

**Option 3: Use BGE's instruction prefix**
```python
# BGE models use query/document prefixes
client.feature_extraction(
    "Represent this sentence for retrieval: My document text",
    model="BAAI/bge-small-en-v1.5"
)
```

**Option 4: prompt_name parameter** (for sentence-transformers with `prompts` config)
```python
client.feature_extraction(
    "What is the capital of France?",
    model="sentence-transformers/all-MiniLM-L6-v2",
    prompt_name="query"  # Prepends "query: " prefix defined in model config
)
```

---

## 7. Batch Processing Patterns

### Small batches (up to ~100 texts per request):
```python
texts = ["text1", "text2", ..., "text100"]
embeddings = client.feature_extraction(texts, model="BAAI/bge-small-en-v1.5")
# Returns (100, max_seq_len, 384)
```

### Large batches — chunk and iterate:
```python
from huggingface_hub import InferenceClient
import numpy as np

client = InferenceClient()

def batch_embed(texts, model="BAAI/bge-small-en-v1.5", batch_size=32):
    """Batch embedding with progress and pooling."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        raw = client.feature_extraction(batch, model=model)
        # Mean-pool each item
        pooled = np.array([emb.mean(axis=0) for emb in raw])
        all_embeddings.append(pooled)
    return np.vstack(all_embeddings)
```

### Rate limit awareness:
- Serverless `hf-inference` has **no documented strict rate limit** per token, but very large batches (>1000 texts) may hit proxy timeouts
- Typical timeout: 60s default (configurable via `InferenceClient(timeout=120)`)
- Stagger batches with small delays if hitting 503 errors:
```python
import time
for batch in batches:
    result = client.feature_extraction(batch)
    time.sleep(0.5)  # Gentle backoff
```

---

## 8. Free Tier Limitations & Workarounds

| Limitation | Impact | Workaround |
|------------|--------|------------|
| No `normalize` support | Output isn't L2-normalized | Normalize client-side: `emb / np.linalg.norm(emb)` |
| No `truncate` support | Long texts may be silently truncated | Pre-truncate to model's context length (512 tokens for most) |
| 60s default timeout | Large batches may timeout | Set `timeout=120` or increase |
| Hidden dimension varies by model | Need to know dim for DB schema | Look up model card or check once `emb.shape[-1]` |
| No persistent vector DB | Need to re-embed on each session | Cache embeddings locally (parquet/npy) |
| Serverless model availability | Models can be loaded/unloaded | First call may be slow (cold start); retry once |

### Cost comparison (free tier vs alternatives):

| Service | Cost | Quality | Latency |
|---------|:----:|:-------:|:-------:|
| **HF Inference API** (hf-inference) | **$0** | Good (BGE models) | ~200-500ms first call, cached subsequent |
| OpenAI `text-embedding-3-small` | $0.02/1M tokens | Excellent | ~100ms |
| Self-hosted TEI (T4 GPU) | ~$0.50/hr GPU | Variable | ~50ms |
| Local llama.cpp embeddings | $0 (if you have hardware) | Good | Depends on hardware |

**Winner for zero-cost:** `hf-inference` with `BAAI/bge-small-en-v1.5` for most use cases.

---

## 9. Practical Patterns: Semantic Search

### Pattern 1: In-memory vector search
```python
import numpy as np
from huggingface_hub import InferenceClient

client = InferenceClient()
MODEL = "BAAI/bge-small-en-v1.5"

def embed_texts(texts):
    raw = client.feature_extraction(texts, model=MODEL)
    return np.array([emb.mean(axis=0) for emb in raw])

def cosine_similarity(a, b):
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b, axis=1)
    return np.dot(a_norm, b_norm.T)

# Index documents
docs = ["Cat likes fish", "Dog likes walks", "Bird sings"]
doc_embs = embed_texts(docs)

# Query
query_emb = embed_texts(["Pet animal"])[0]
scores = cosine_similarity(query_emb, doc_embs)
best_idx = np.argmax(scores)
print(f"Best match: {docs[best_idx]} (score: {scores[best_idx]:.3f})")
```

### Pattern 2: RAG chunk retrieval
```python
def retrieve_relevant_chunks(query: str, chunks: list[str], top_k: int = 3):
    """Retrieve top-k chunks for a query using serverless embeddings."""
    # Embed all chunks
    chunk_embs = embed_texts(chunks)
    # Embed query
    query_emb = embed_texts([query])[0]
    # Score
    scores = cosine_similarity(query_emb, chunk_embs)
    top_indices = np.argsort(scores[0])[::-1][:top_k]
    return [(chunks[i], float(scores[0][i])) for i in top_indices]
```

### Pattern 3: Using sentence_similarity for direct comparison
```python
def rank_documents(query: str, documents: list[str]):
    """Direct ranking via sentence_similarity."""
    scores = client.sentence_similarity(
        query,
        other_sentences=documents,
        model="sentence-transformers/all-MiniLM-L6-v2"
    )
    ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
    return ranked
```

---

## 10. OpenAI-Compatible Embedding Endpoints

The InferenceClient supports OpenAI-compatible embedding endpoints via the `base_url` parameter:

```python
# Using an OpenAI-compatible endpoint
client = InferenceClient(
    base_url="https://api.openai.com/v1",  # or any OpenAI-compatible
    api_key="sk-..."                       # or token=...
)

# Now feature_extraction supports OpenAI-specific params:
emb = client.feature_extraction(
    "Hello world",
    model="text-embedding-3-small",
    dimensions=256,              # Truncate to 256 dims
    encoding_format="float"      # or "base64"
)
```

**Parameters unique to OpenAI-compatible endpoints:**
- `dimensions` — Request fewer dimensions than the model's full output
- `encoding_format` — `"float"` (default) or `"base64"` (smaller payload)

When `base_url` is set, the client uses the OpenAI provider instead of hf-inference, which maps to OpenAI's `/v1/embeddings` endpoint.

---

## 11. Caching & Persistence

For zero-cost semantic search that survives session restarts:

```python
import numpy as np
import json

def save_embeddings(embeddings: np.ndarray, texts: list[str], path: str):
    """Save embeddings + texts to disk."""
    np.save(f"{path}/embeddings.npy", embeddings)
    with open(f"{path}/texts.json", "w") as f:
        json.dump(texts, f)

def load_embeddings(path: str):
    """Load embeddings + texts from disk."""
    embeddings = np.load(f"{path}/embeddings.npy")
    with open(f"{path}/texts.json") as f:
        texts = json.load(f)
    return embeddings, texts
```

For larger datasets, consider **parquet** format:
```python
import pyarrow as pa
import pyarrow.parquet as pq

table = pa.table({
    "text": texts,
    "embedding": [emb.tobytes() for emb in embeddings]  # serialize as bytes
})
pq.write_table(table, "embeddings.parquet")
```

---

## 12. Comparison: feature_extraction vs sentence_similarity

| Aspect | `feature_extraction` | `sentence_similarity` |
|--------|:--------------------:|:---------------------:|
| Returns | Raw embeddings (np.ndarray) | Pre-computed scores (list[float]) |
| Pooling | Per-token (you pool) | Pooled (server-side) |
| Storage | Cacheable for later search | One-shot comparison |
| Use case | Vector DB, clustering, RAG | Direct ranking, Q&A |
| Cost per call | Same (1 inference call) | Same |
| Batch support | ✅ list[str] | ❌ single sentence vs list |
| Default model | `facebook/bart-base` | `sentence-transformers/all-MiniLM-L6-v2` |

**Rule of thumb:** Use `feature_extraction` when you need to **store** embeddings for later. Use `sentence_similarity` for **one-off** comparisons.

---

## 13. Model Selection Guide

| Use Case | Recommended Model | Dimensions | Why |
|----------|:-----------------:|:----------:|:----|
| English semantic search (fast) | `BAAI/bge-small-en-v1.5` | 384 | Fast, good quality, 67M downloads |
| English semantic search (quality) | `BAAI/bge-base-en-v1.5` | 768 | Better quality than small |
| English semantic search (best) | `mixedbread-ai/mxbai-embed-large-v1` | 1024 | Top quality, larger |
| Multilingual | `intfloat/multilingual-e5-large` | 1024 | 100+ languages |
| Modern multilingual | `Qwen/Qwen3-Embedding-0.6B` | 1792 | Newer architecture, 0.6B params |
| Reranking | `BAAI/bge-reranker-large` | N/A (cross-encoder) | Use `text-classification` not `feature-extraction` |
| Sentence similarity | `sentence-transformers/all-MiniLM-L6-v2` | 384 | Default, reliable |

---

## 14. Error Handling

```python
from huggingface_hub import InferenceClient, InferenceTimeoutError, HfHubHTTPError

client = InferenceClient()

def safe_embed(texts, model="BAAI/bge-small-en-v1.5", retries=2):
    for attempt in range(retries + 1):
        try:
            return client.feature_extraction(texts, model=model)
        except InferenceTimeoutError:
            if attempt < retries:
                time.sleep(2 ** attempt)  # exponential backoff
                continue
            raise
        except HfHubHTTPError as e:
            if e.response.status_code == 503 and attempt < retries:
                # Model loading — retry after brief wait
                time.sleep(5)
                continue
            raise
```

---

## 15. Source Code Reference

Key files in `huggingface_hub`:

| File | What it contains |
|------|-----------------|
| `inference/_client.py` | `InferenceClient.feature_extraction()` and `.sentence_similarity()` methods |
| `inference/_providers/__init__.py` | `PROVIDERS` dict, `get_provider_helper()` — routing logic |
| `inference/_providers/hf_inference.py` | `HFInferenceFeatureExtractionTask` — /pipeline/{task} URL logic |
| `inference/_providers/openai.py` | OpenAI-compatible embeddings (dimensions, encoding_format) |

Key URLs:
- `GET https://huggingface.co/api/tasks` — Recommended models per task
- `GET https://huggingface.co/api/models/{model_id}/inference-providers` — Provider routing for a model
- `POST https://api-inference.huggingface.co/models/{model_id}/pipeline/feature-extraction` — Embeddings endpoint
- `POST https://api-inference.huggingface.co/models/{model_id}/pipeline/sentence-similarity` — Similarity endpoint
