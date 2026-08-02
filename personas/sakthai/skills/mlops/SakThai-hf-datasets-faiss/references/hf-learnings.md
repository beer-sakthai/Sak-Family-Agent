# HF Learnings — Datasets FAISS Integration

**Topic:** hf-datasets-faiss-vector-search-deep-dive
**Date:** 2026-07-24
**author:** SakThai
**license:** MIT

## Overview

The Hugging Face `datasets` library provides first-class integration with Meta's **FAISS** (Facebook AI Similarity Search) library for efficient similarity search on dataset columns containing vector embeddings. This allows datasets to function as **vector databases** for nearest-neighbor search, retrieval-augmented generation (RAG), deduplication, and clustering workflows.

## Core API Reference

### Adding Indexes

#### `Dataset.add_faiss_index()`

Adds a FAISS index to a column. Operates **in-place** on the dataset.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `column` | `str` | required | Column name containing vector embeddings |
| `index_name` | `str` | `column` | Logical identifier for the index |
| `device` | `int`, `list[int]`, `None` | `None` | GPU device(s): positive int = single GPU, negative = all GPUs, list = specific GPUs |
| `string_factory` | `str` | `None` | FAISS factory string for index type (e.g., `"IVF100,Flat"`) |
| `metric_type` | `int` | `None` | `faiss.METRIC_L2` (default if None) or `faiss.METRIC_INNER_PRODUCT` |
| `custom_index` | `faiss.Index` | `None` | Pre-configured FAISS index instance |
| `batch_size` | `int` | `1000` | Number of vectors added per batch |
| `train_size` | `int` | `None` | Vectors used for index training (required for IVF-type indexes) |
| `faiss_verbose` | `bool` | `False` | Enable FAISS verbose logging |
| `dtype` | `np.dtype` | `np.float32` | NumPy dtype for vector storage |

**Index types via `string_factory`:**

| Factory String | Index Type | Properties |
|---|---|---|
| `None` (default) | `IndexFlatL2` | Exact search, brute-force, O(n) per query |
| `"IVF100,Flat"` | Inverted File + Flat | Approximate, 100 centroids, 10x–100x faster |
| `"IVF100,PQ8"` | IVF + Product Quantization | Compressed vectors, lower memory |
| `"HNSW64"` | Hierarchical Navigable Small World | Graph-based, high recall, fast |
| `"HNSW32,PQ8"` | HNSW + PQ | Memory-efficient graph search |

**GPU Considerations:**
- Single GPU: `device=0`
- All GPUs: `device=-1`
- Specific GPUs: `device=[0, 1, 2]`
- Index is trained and added on GPU, but queries run on the same device
- GPU indexes use different FAISS index implementations internally (GpuIndexFlat, GpuIndexIVF, etc.)

### Querying

#### `Dataset.get_nearest_examples(index_name, query, k)`

Retrieves the `k` closest examples to the query vector.

- **Returns:** `(scores, retrieved_examples)`
  - `scores`: list of distances/similarities
  - `retrieved_examples`: dict of column_name → list of values (like a dataset slice)

#### `Dataset.search(index_name, query, k)`

Returns indices and scores only (no full examples).

- **Returns:** `(scores, indices)`

**Example:**
```python
from datasets import load_dataset
from transformers import DPRQuestionEncoder, DPRQuestionEncoderTokenizer
import numpy as np

# Load dataset
ds = load_dataset('community-datasets/crime_and_punish', split='train[:100]')

# Add FAISS index on an embeddings column
ds.add_faiss_index(column='embeddings', index_name='dp_embeddings')

# Query with a question embedding
q_encoder = DPRQuestionEncoder.from_pretrained("facebook/dpr-question_encoder-single-nq-base")
q_tokenizer = DPRQuestionEncoderTokenizer.from_pretrained("facebook/dpr-question_encoder-single-nq-base")
question = "Is it serious?"
query_embedding = q_encoder(**q_tokenizer(question, return_tensors="pt"))[0][0].numpy()

# Search
scores, retrieved = ds.get_nearest_examples('embeddings', query_embedding, k=10)
retrieved["line"][0]
# 'that_ serious? It is not serious at all.'
```

### Persistence

#### `Dataset.save_faiss_index(index_name, file)`

Serializes the FAISS index to disk. The index file contains the raw FAISS index data (not the dataset rows).

#### `Dataset.load_faiss_index(index_name, file, device, storage_options)`

Loads a previously saved FAISS index and attaches it to the dataset.

**Remote URI support** (since datasets v2.11.0):
```python
# Load from S3
ds.load_faiss_index('embeddings', 's3://my-bucket/index.faiss',
                    storage_options={'key': '...', 'secret': '...'})

# Load from HTTP
ds.load_faiss_index('embeddings', 'https://example.com/index.faiss')
```

**Workflow:**
```python
# Save
ds.save_faiss_index('embeddings', 'my_index.faiss')

# Later, load
ds = load_dataset('community-datasets/crime_and_punish', split='train[:100]')
ds.load_faiss_index('embeddings', 'my_index.faiss')
# Now ds.get_nearest_examples() works without rebuilding the index
```

### Advanced: Direct FAISS Index Access

```python
faiss_index = ds.get_index('embeddings').faiss_index

# Range search — find all vectors within a distance threshold
limits, distances, indices = faiss_index.range_search(
    x=query_embedding.reshape(1, -1),
    thresh=0.95
)
```

### Managing Indexes

```python
# Drop an index to free memory
ds.drop_index('embeddings')

# List available indexes
print(ds.list_indexes())  # may not exist in all versions

# Check if index exists
ds.get_index('embeddings')  # raises KeyError if missing
```

## Comparison: FAISS vs Elasticsearch

| Feature | FAISS | Elasticsearch |
|---|---|---|
| Search type | Vector similarity (ANN/exact) | Text keyword + BM25 |
| Column type | Embedding vectors (float arrays) | Text strings |
| Storage | On-disk `.faiss` file | External Elasticsearch server |
| Speed | ms-scale for millions of vectors | Depends on index size |
| Accuracy | Approximate (ANN) or exact | Exact match + ranking |
| Setup | No external service needed | Requires running ES cluster |
| Use case | RAG, semantic search, dedup | Full-text search, keyword match |

## Practical Patterns

### Pattern 1: RAG Pipeline

```python
# 1. Generate embeddings for corpus
corpus = load_dataset("my-corpus", split="train")
corpus = corpus.map(lambda x: {"emb": embed_fn(x["text"])})

# 2. Index
corpus.add_faiss_index("emb", metric_type=faiss.METRIC_INNER_PRODUCT)

# 3. Query at inference
query_emb = embed_fn(user_query)
scores, docs = corpus.get_nearest_examples("emb", query_emb, k=5)
```

### Pattern 2: IVF with Training

```python
# IVF indexes need training (clustering)
ds.add_faiss_index(
    column="embeddings",
    string_factory="IVF100,Flat",
    train_size=10000,        # Use 10k vectors for k-means training
    metric_type=faiss.METRIC_L2
)

# nprobe controls accuracy-speed tradeoff
ds.get_index("embeddings").faiss_index.nprobe = 10
```

### Pattern 3: Custom Pre-built Index

```python
import faiss

# Build a custom index
dim = 768
index = faiss.IndexHNSWFlat(dim, 64)
index.hnsw.efConstruction = 200

# Add to dataset
ds.add_faiss_index(column="embeddings", custom_index=index)
```

## Known Limitations & Pitfalls

1. **Index is detached from dataset rows when saved** — only the FAISS vector index is saved, not the dataset. You must reload both separately.
2. **Column dtype mismatch** — vectors must be numeric arrays; FAISS auto-casts to `float32`.
3. **Not serialized with dataset** — `ds.save_to_disk()` does NOT save FAISS indexes. Use `save_faiss_index()` separately.
4. **GPU indexes are not serializable** — must be transferred to CPU before saving (convert with `faiss.index_gpu_to_cpu()`).
5. **Memory** — FAISS loads the entire index into memory. For billion-scale datasets, use disk-based or memory-mapped indexes.
6. **Thread safety** — FAISS indexes are not thread-safe for concurrent writes.

## Version History

| datasets version | Feature |
|---|---|
| v1.2.0 | Initial FAISS integration |
| v2.4.0 | `batch_size` parameter added |
| v2.11.0 | Remote URI support in `load_faiss_index()` |

## References

- [HF Datasets: Search Index (FAISS + ES)](https://huggingface.co/docs/datasets/main/en/faiss_es)
- [Datasets API: add_faiss_index](https://huggingface.co/docs/datasets/v4.8.4/en/package_reference/main_classes#datasets.Dataset.add_faiss_index)
- [FAISS GitHub](https://github.com/facebookresearch/faiss)
- [FAISS Wiki (index types)](https://github.com/facebookresearch/faiss/wiki/The-index-factory)
