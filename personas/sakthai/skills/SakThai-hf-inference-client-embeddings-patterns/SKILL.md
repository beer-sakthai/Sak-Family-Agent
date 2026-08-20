---
name: SakThai-hf-inference-client-embeddings-patterns
description: 'name: SakThai-hf-inference-client-embeddings-patterns'
---

# HF Inference Client — Embeddings Patterns (Serverless)

## Overview
Generate text embeddings via the Hugging Face Inference API at zero cost using `InferenceClient.feature_extraction()` and `InferenceClient.sentence_similarity()`. Covers the serverless (hf-inference) provider, OpenAI-compatible endpoints, and practical patterns for semantic search, clustering, and RAG on a budget.

**Key capabilities:**

| Method | Returns | Use Case |
|--------|---------|----------|
| `feature_extraction(text)` | `np.ndarray` (float32) | Raw embeddings for vector DBs, clustering, similarity |
| `sentence_similarity(sentence, other_sentences)` | `list[float]` (scores) | Direct pairwise similarity comparison |

**Zero-cost:** Serverless inference via `hf-inference` provider is free with a HF token. No GPU needed. See `references/hf-learnings.md` for full API reference, provider routing details, and advanced patterns.

## Quick Start
```python
from huggingface_hub import InferenceClient

client = InferenceClient()  # uses HF_TOKEN from env

# Single text embedding
embedding = client.feature_extraction("Hello world")
# shape: (sequence_length, hidden_dim)

# Batch embedding
batch = client.feature_extraction(["Hello", "World", "Embed me"])
# shape: (3, sequence_length, hidden_dim)

# Sentence similarity
scores = client.sentence_similarity(
    "I love machine learning",
    other_sentences=["ML is great", "I hate math", "Deep learning rocks"]
)
# [0.91, 0.12, 0.88]
```

## Best Practices
1. **Specify model explicitly** — don't rely on default (currently `facebook/bart-base`); use `BAAI/bge-small-en-v1.5` or `sentence-transformers/all-MiniLM-L6-v2` for quality
2. **Pool embeddings** — most sentence-transformers output per-token vectors; use `mean` or `cls` pooling for sentence-level embeddings
3. **Normalize** — set `normalize=True` for cosine similarity
4. **Batch** — pass `list[str]` to batch efficiently within payload size limits (check model max tokens)
5. **Use `sentence_similarity`** instead of manual cosine for direct comparison — it's handled server-side
