---
name: SakThai-hf-datasets-faiss
description: A skill for Hf Datasets Faiss.
...
---

# SKILL.md — hf-datasets-faiss

author: SakThai
license: MIT

**author:** SakThai  
**license:** MIT  
**tags:** [huggingface, datasets, faiss, vector-search, nearest-neighbors, embeddings]  
**domain:** mlops  

## Purpose

Expert knowledge on FAISS vector search integration in Hugging Face Datasets. Covers creating, querying, saving, and loading FAISS indexes on Dataset columns for fast approximate and exact nearest-neighbor search.

## Commands

```python
# Add a FAISS index to a Dataset column
ds.add_faiss_index(
    column="embeddings",           # column with vectors (list/array of floats)
    index_name="my_index",         # optional name for the index
    device=None,                   # GPU ID (int/list) for GPU-accelerated indexing
    string_factory=None,           # FAISS factory string e.g. "IVF100,Flat"
    metric_type=None,              # faiss.METRIC_INNER_PRODUCT or faiss.METRIC_L2
    custom_index=None,             # pre-built faiss.Index instance
    batch_size=1000,               # vectors added in batches
    train_size=None,               # num vectors for training (clustering)
    faiss_verbose=False,
    dtype=np.float32
)

# Query nearest examples
scores, results = ds.get_nearest_examples("embeddings", query_vector, k=10)

# Search (returns indices + scores)
scores, indices = ds.search("embeddings", query_vector, k=10)

# Save to disk
ds.save_faiss_index("embeddings", "my_index.faiss")

# Load from disk / remote URI
ds.load_faiss_index("embeddings", "my_index.faiss", device=0)
ds.load_faiss_index("embeddings", "s3://bucket/index.faiss", storage_options={...})

# Access raw FAISS index for advanced ops
faiss_index = ds.get_index("embeddings").faiss_index
limits, distances, indices = faiss_index.range_search(query_embedding, thresh=0.95)

# Drop an index
ds.drop_index("embeddings")
```

## Key Details

- **Default index:** `IndexFlat` (exact L2 search, brute-force — accurate but O(n) per query)  
- **Factory strings** create approximate indexes: `"IVF100,Flat"` (inverted file + flat), `"HNSW64"` (hierarchical navigable small world), `"PQ16"` (product quantization)  
- **GPU support:** pass `device=0` for single GPU, `-1` for all GPUs, `[0,1]` for specific GPUs  
- **Metric types:** `faiss.METRIC_L2` (Euclidean distance, default) or `faiss.METRIC_INNER_PRODUCT` (cosine similarity equivalent with normalized vectors)  
- **Batch_size** = 1000 by default, vectors are added in chunks to avoid OOM  
- **train_size** must be set for IVF/IndexIVF indexes (cluster training step)  
- **Persistence:** saved indexes are serialized FAISS files (`.faiss`), loadable later without recomputing  
- **Remote loading:** since datasets v2.11.0, `load_faiss_index` supports S3/remote URIs with `storage_options`  
- **dtype** defaults to `np.float32`; vectors are auto-cast

## Related Skills

- `hf-datasets-library` — base datasets library
- `hf-datasets-streaming-iterable-dataset` — streaming with embedding generation
- `hf-sentence-transformers` — sentence embeddings commonly used as FAISS vectors

## Version Compatibility

- FAISS integration available since `datasets` v1.2.0
- Remote URI support added in v2.11.0
- `range_search` exposed via `.get_index().faiss_index`
