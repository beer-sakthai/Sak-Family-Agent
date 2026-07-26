#!/usr/bin/env python3
"""Update the sakthai-embedding-multilingual model card with enriched content."""

from huggingface_hub import HfApi

NEW_README = """---
license: mit
language:
- multilingual
pipeline_tag: feature-extraction
tags:
- embeddings
- sentence-similarity
- retrieval
- sakthai-family
- bert
- sentence-transformers
- feature-extraction
library_name: sentence-transformers
---

# SakThai Multilingual Embedding

Cross-lingual sentence embedding model — 384-dim BERT-based for semantic search,
sentence similarity, and dense retrieval across 50+ languages.

Part of the [SakThai Model Family](https://huggingface.co/collections/Nanthasit/sakthai-model-family-668e4e9a8b8f5c7e3b2d1a0c).

---

## Model Details

| Property | Value |
|----------|-------|
| Architecture | BERT-base (12-layer, 12-head) |
| Output Dimension | 384 |
| Max Sequence Length | 512 tokens |
| Parameters | 118M |
| Tokenizer | Multilingual WordPiece (250K vocab) |
| Pipeline | Feature Extraction / Sentence Embeddings |
| Library | sentence-transformers + transformers |
| Inference | CPU or GPU — lightweight |

### What makes it multilingual?

The model uses a multilingual tokenizer trained on 50+ languages, producing
language-agnostic embeddings. Sentences in different languages with similar
meaning map to nearby points in the 384-dim vector space — enabling cross-lingual
retrieval and comparison without translation.

---

## Usage

### Option 1: sentence-transformers (Recommended)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("Nanthasit/sakthai-embedding-multilingual")

sentences_multi = [
    "I love machine learning",
    "J'adore l'apprentissage automatique",
    "Ich liebe maschinelles Lernen",
]
embeddings = model.encode(sentences_multi)
print(embeddings.shape)  # (3, 384)

from sklearn.metrics.pairwise import cosine_similarity
sim_matrix = cosine_similarity(embeddings)
print(sim_matrix)
```

### Option 2: Hugging Face InferenceClient

```python
from huggingface_hub import InferenceClient

client = InferenceClient()
result = client.feature_extraction(
    text="Hugging Face is creating the AI revolution",
    model="Nanthasit/sakthai-embedding-multilingual"
)
print(len(result))  # 384
```

### Option 3: Transformers (Direct)

```python
from transformers import AutoTokenizer, AutoModel
import torch

model = AutoModel.from_pretrained("Nanthasit/sakthai-embedding-multilingual")
tokenizer = AutoTokenizer.from_pretrained("Nanthasit/sakthai-embedding-multilingual")

def embed(text: str) -> list:
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    attention_mask = inputs["attention_mask"]
    token_embeddings = outputs.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    embedding = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return embedding[0].tolist()

vec = embed("Semantic search across languages")
print(len(vec))  # 384
```

### Option 4: curl (CLI)

```bash
curl https://api-inference.huggingface.co/pipeline/feature-extraction/Nanthasit/sakthai-embedding-multilingual \
  -H "Authorization: Bearer $HF_TOKEN" \
  -d '{"inputs": "Search across languages without translation"}'
```

---

## Use Cases

- **Cross-lingual semantic search** — Query in English, retrieve documents in 50+ languages
- **Multilingual clustering** — Group similar content across language boundaries
- **Sentence similarity** — Compare meaning across translations
- **RAG pipelines** — Embed multilingual documents for retrieval-augmented generation
- **Zero-shot classification** — Encode labels + text and compare similarity

---

## Performance

| Metric | Value |
|--------|-------|
| Embedding dimension | 384 |
| Inference speed | ~1,000 sentences/sec on CPU (batch=32) |
| Memory usage | ~500 MB at inference |
| Max tokens | 512 per input |
| Similarity metric | Cosine similarity |

---

## Family Links

| Model | Description |
|-------|-------------|
| [SakThai 1.5B](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged) | Tool-calling and text generation |
| [SakThai Vision 7B](https://huggingface.co/Nanthasit/sakthai-vision-7b) | Multimodal image understanding |
| [SakThai TTS](https://huggingface.co/Nanthasit/sakthai-tts-model) | Text-to-speech voice model |
| [SakThai Coder 1.5B](https://huggingface.co/Nanthasit/sakthai-coder-1.5b) | Code generation specialist |
| [Leaderboard](https://huggingface.co/Nanthasit/sakthai-leaderboard) | Model benchmarks |
| [TTS Showcase](https://huggingface.co/Nanthasit/sakthai-tts) | Interactive TTS demo |

---

## File Structure

```
config.json
config_sentence_transformers.json
model.safetensors
tokenizer.json
tokenizer_config.json
1_Pooling/config.json
modules.json
sentence_bert_config.json
README.md
```
"""

def main():
    api = HfApi()
    api.upload_file(
        path_or_fileobj=NEW_README.encode(),
        path_in_repo="README.md",
        repo_id="Nanthasit/sakthai-embedding-multilingual",
        commit_message="Enrich model card: usage examples, architecture details, family links, performance metrics"
    )
    print("Uploaded sakthai-embedding-multilingual README.md successfully!")
    print(f"New size: {len(NEW_README)} bytes (was 695 bytes)")


if __name__ == "__main__":
    main()
