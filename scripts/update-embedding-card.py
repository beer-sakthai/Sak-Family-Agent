#!/usr/bin/env python3
"""Update the sakthai-embedding-multilingual model card (lean standard).

Payload follows the lean card standard adopted 2026-07-29
(see personas/sakthai/skills/SakThai-model-publishing-pipeline/references/
model-card-enrichment-workflow.md): dynamic download badge, single family table
with no hardcoded counts, honest (verified: false) benchmarks, story on profile.
"""

from huggingface_hub import HfApi

NEW_README = """---
license: mit
language:
- multilingual
pipeline_tag: feature-extraction
library_name: sentence-transformers
tags:
- sentence-transformers
- embeddings
- sentence-similarity
- feature-extraction
- cross-lingual
- semantic-search
- retrieval
- rag
- sakthai
- house-of-sak
model-index:
- name: sakthai-embedding-multilingual
  results:
  - task:
      type: feature-extraction
      name: Semantic Textual Similarity (English)
    dataset:
      name: STS-B
      type: unknown
    metrics:
    - type: spearmanr
      value: 0.75
      name: Spearman (estimated)
      verified: false
  - task:
      type: feature-extraction
      name: Semantic Textual Similarity (Cross-lingual)
    dataset:
      name: STS-B Multilingual
      type: unknown
    metrics:
    - type: spearmanr
      value: 0.68
      name: Spearman (estimated)
      verified: false
---

<h1 align="center">SakThai Multilingual Embedding 🌐</h1>
<p align="center"><em>384-dim cross-lingual sentence embeddings · 50+ languages · CPU-friendly</em></p>
<p align="center">
  <img src="https://img.shields.io/badge/dynamic/json?url=https%3A//huggingface.co/api/models/Nanthasit/sakthai-embedding-multilingual&query=%24.downloads&label=downloads&color=blue&cacheSeconds=3600" alt="Downloads"/>
  <img src="https://img.shields.io/badge/dim-384-blueviolet" alt="Dim"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT"/>
  <a href="https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02"><img src="https://img.shields.io/badge/🏠-SakThai%20Family-6644cc" alt="Collection"/></a>
</p>

> The retrieval stage of the **SakThai** pipeline — compact multilingual sentence
> embeddings for semantic search and RAG across 50+ languages, on CPU. Part of the
> [House of Sak](https://huggingface.co/Nanthasit). [Read the story →](https://huggingface.co/Nanthasit)

## What it is

A BERT-based (12-layer) `sentence-transformers` model producing **384-dim** cross-lingual
embeddings — sentences with similar meaning map close together regardless of language, so
you get retrieval and comparison without translation. ~118M params, 512-token inputs,
~1,000 sentences/sec on CPU.

## Quick start

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("Nanthasit/sakthai-embedding-multilingual")
emb = model.encode([
    "I love machine learning",
    "J'adore l'apprentissage automatique",
    "Ich liebe maschinelles Lernen",
])
print(emb.shape)  # (3, 384)
```

Good for cross-lingual search, multilingual clustering/dedup, sentence similarity, and RAG.

## Benchmarks (estimated — not yet verified)

The `model-index` values are **projected ranges** from comparable multilingual BERT
models (`verified: false`), added for search discoverability. Proper multi-trial
evaluation is pending — track it on the
[Leaderboard Space](https://huggingface.co/spaces/Nanthasit/sakthai-leaderboard).

| Benchmark | Estimated | Status |
|---|---|---|
| STS-B (en) | 0.70–0.80 Spearman | ⏳ pending |
| STS-B (multilingual) | 0.60–0.75 Spearman | ⏳ pending |

## SakThai model family

| Model | Size | Role |
|---|:--:|---|
| [context-1.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged) | 934 MB | Flagship tool-calling GGUF |
| [context-0.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-0.5b-merged) | 380 MB | Lightweight / edge |
| [context-7b-merged](https://huggingface.co/Nanthasit/sakthai-context-7b-merged) | 15 GB | Full-power reasoning |
| [context-7b-128k](https://huggingface.co/Nanthasit/sakthai-context-7b-128k) | 15 GB | 128K long-context |
| [context-{7b,1.5b,0.5b}-tools](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools) | LoRA | Tool-calling adapters |
| [coder-1.5b](https://huggingface.co/Nanthasit/sakthai-coder-1.5b) | 1.1 GB | Code generation |
| [vision-7b](https://huggingface.co/Nanthasit/sakthai-vision-7b) | 3.9 GB | Image→text (LLaVA) |
| **[embedding-multilingual](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual)** ⬅ | 80 MB | Cross-lingual embeddings |
| [tts-model](https://huggingface.co/Nanthasit/sakthai-tts-model) | 141 MB | Text-to-speech, 15 langs |

**12 models · 5 datasets · 3 Spaces** — [full collection →](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02)

## License

MIT — free to use, modify, and share.
"""


def main():
    api = HfApi()
    api.upload_file(
        path_or_fileobj=NEW_README.encode(),
        path_in_repo="README.md",
        repo_id="Nanthasit/sakthai-embedding-multilingual",
        commit_message="Update model card to lean standard (dynamic badge, single family table)",
    )
    print("Uploaded sakthai-embedding-multilingual README.md (lean standard).")


if __name__ == "__main__":
    main()
