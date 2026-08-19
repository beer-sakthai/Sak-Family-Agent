---
name: SakThai-hf-sentence-transformers
description: "Hugging Face sentence-transformers library — embedding models, semantic search, sentence similarity, Cross-Encoders / rerankers, Sparse Encoders, MTEB leaderboard, and training custom embedding models. Covers library v5.x+, Python 3.10+."
---

# HF Sentence Transformers — Embeddings, Retrieval & Reranking

## Overview

`sentence-transformers` (now maintained under the Hugging Face org at
`github.com/huggingface/sentence-transformers`) provides embedding generation,
semantic similarity, retrieval, and reranking using state-of-the-art transformer
models. The library supports three model types:

| Model Type | Purpose | Output |
|---|---|---|
| **SentenceTransformer** | Dense embedding vectors for sentences/text | Fixed-size vector per text |
| **CrossEncoder** | Reranker — pairwise similarity/score | Single similarity score |
| **SparseEncoder** | Sparse bag-of-words embeddings | Sparse vector (word weights) |

## Installation

```bash
pip install -U sentence-transformers
```

Requires Python >=3.10, PyTorch >=1.11.0, transformers >=4.41.0.

Extras: `[image]`, `[audio]`, `[video]`, `[train]`, `[onnx]`, `[openvino]`, `[dev]`.

For uv or conda see [Installation docs](https://www.sbert.net/docs/installation.html).

## Quickstart — SentenceTransformer (Dense Embeddings)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

sentences = [
    "The weather is lovely today.",
    "It's so sunny outside!",
    "He drove to the stadium.",
]
embeddings = model.encode(sentences)
# embeddings.shape == (3, 384) for MiniLM-L6-v2

from sentence_transformers.util import cos_sim
sim = cos_sim(embeddings[0], embeddings[1])
```

## Quickstart — CrossEncoder (Reranker)

```python
from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
pairs = [
    ("What is Python?", "Python is a programming language."),
    ("What is Python?", "Monty Python is a comedy group."),
]
scores = model.predict(pairs)
```

## Quickstart — SparseEncoder

```python
from sentence_transformers import SparseEncoder

model = SparseEncoder("prithivida/Splade_PP_en_v1")
embeddings = model.encode(sentences)
```

## Key Concepts

### 1. Model Hub

Over 15,000 pre-trained models tagged with `library:sentence-transformers` on
[HF Hub](https://huggingface.co/models?library=sentence-transformers).

Top models by downloads (July 2026):

| Model | Downloads | Pipeline |
|---|---|---|
| `all-MiniLM-L6-v2` | 254M+ | sentence-similarity |
| `paraphrase-multilingual-MiniLM-L12-v2` | 51M+ | sentence-similarity |
| `all-mpnet-base-v2` | 29M+ | sentence-similarity |

### 2. MTEB Leaderboard

The [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) ranks
embedding models across 8 task categories (clustering, pair classification,
reranking, retrieval, STS, summarization, classification, bitext mining)
using 56+ datasets.

### 3. Training

sentence-transformers supports training/fine-tuning:
- Dense embeddings: contrastive loss, triplet loss, multiple negatives ranking loss
- Rerankers: CrossEncoder fine-tuning on pairwise data
- Sparse encoders: SparseEncoder training with FLOPs regularization

See [Training Overview](https://sbert.net/docs/sentence_transformer/training_overview.html).

### 4. Applications

- Semantic Search: encode query + corpus -> cosine similarity -> top-k
- Semantic Textual Similarity (STS): measure sentence pair similarity
- Paraphrase Mining: find paraphrases in large text collections
- RAG: embed documents for vector DB retrieval

## Pitfalls

1. **Normalization**: By default `model.encode()` returns normalized vectors with
   `normalize_embeddings=True`. Use `normalize_embeddings=False` for dot-product models.
2. **Batch size**: Large batches can OOM. Use `model.encode(batch_size=32)`.
3. **Mixed precision**: Use `model.half()` for FP16 inference on compatible GPUs.
4. **CrossEncoder != SentenceTransformer**: CrossEncoder takes pairs, SentenceTransformer takes single texts.
5. **Model naming**: Always use the full HF Hub ID.
6. **Training memory**: Use LoRA via PEFT for efficient fine-tuning of large models.
7. **Uploading to HF requires ALL config files**: When uploading via `api.upload_folder()`, `IndexError: index out of range in self` means tokenizer config files are missing from the Hub repo. Fix: upload ALL files from the model directory — `tokenizer.json`, `tokenizer_config.json`, `config.json`, `vocab.txt`, `special_tokens_map.json`, `modules.json`, `config_sentence_transformers.json` — not just weights. `model.save()` handles this correctly; `api.upload_file()` needs explicit upload of each config file. Always verify after upload by loading back from HF and encoding a test sentence.

## Reference Files

- `references/quickstart.py` — Runnable Python snippets for all 3 model types
- `references/hf-ecosystem-facts.md` — Live API research data (PyPI stats, GitHub stats, top-10 model rankings, July 2026)
- `references/rag-agent-knowledge.md` — Build a RAG semantic search system over agent SOULs and skills: embedding, index storage, HTTP query API, memory management, pitfalls.

## Links

- Docs: https://www.SBERT.net
- GitHub: https://github.com/huggingface/sentence-transformers
- HF Models: https://huggingface.co/models?library=sentence-transformers
- MTEB: https://huggingface.co/spaces/mteb/leaderboard
- PyPI: https://pypi.org/project/sentence-transformers/
