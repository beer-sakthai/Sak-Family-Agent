---
name: SakThai-hf-cosmopedia
author: SakThai
license: MIT
description: Complete reference on HuggingFace Cosmopedia — the synthetic dataset generation pipeline for pre-training LLMs, covering v1 and v2, prompt engineering, large-scale generation with llm-swarm, deduplication/decontamination, and integration with SmolLM training.
version: 1.0.0
category: mlops
---

# HF Cosmopedia — Synthetic Dataset Generation at Scale

Trigger when: user asks about synthetic data generation, Cosmopedia, SmolLM training data, llm-swarm, datatrove deduplication, benchmark decontamination, or how to create large-scale pre-training datasets.

## Overview

Cosmopedia is Hugging Face's open-source pipeline for generating massive synthetic datasets for pre-training LLMs. It was designed to replicate and open-source the methodology behind Microsoft's Phi-1.5 "Textbooks Are All You Need" approach.

| Version | Tokens | Generator Model | Date | Used In |
|---------|--------|-----------------|------|---------|
| v1 | 25B | Mixtral-8x7B-Instruct-v0.1 | Mar 2024 | cosmo-1b |
| v2 | 28B | Mixtral-8x7B-Instruct-v0.1 | Jul 2024 | SmolLM-135M/360M/1.7B |

**Key characteristics:**
- Fully open: code, dataset, and trained models are all Apache-2.0 licensed
- Contains over 30 million files and 25+ billion tokens
- Largest open synthetic pre-training dataset to date
- Covers 100+ topics across 8 subsets
- Generated using open-source Mixtral (not proprietary GPT-4)

## Architecture

Cosmopedia uses a multi-stage pipeline:

```
Topic Sources (curated + web) 
    → Prompt Construction 
    → Large-Scale Generation (llm-swarm + TGI) 
    → Deduplication (datatrove MinHash) 
    → Decontamination (n-gram benchmark filter) 
    → Evaluation (lighteval)
```

## Pipeline Components

### 1. Prompts (`prompts/` directory)

Prompts are built from two types of seed data:

**Curated Sources** (scalability-limited but high quality):
- **Stanford courses**: Outline extraction from 250K+ courses, prompt asks model to generate textbooks per unit
- **Khan Academy**: Educational exercises and articles
- **OpenStax**: Open textbooks with 16K unique units extracted  
- **WikiHow**: How-to articles
- **AutoMathText**: Curated mathematical texts for scientific content

**Web Data** (80%+ of prompts, scalable):
- 145 topic clusters computed from **RefinedWeb** (or FineWeb for v2)
- Each cluster labeled by Mixtral with topic + educational score (0-10)
- 112 educational topics retained after filtering low-value clusters
- Prompts condition on topic only 50% of the time for diversity
- ~23 million prompts built from web data

**Diversity via Audience × Style Matrix:**
- 4 audiences: young children, high school, college students, researchers/professionals
- 3 styles: textbook, blog post, WikiHow article
- Up to 12× prompt multiplication per topic

**Instruction datasets for stories:**
- **UltraChat** "Questions about the world" subset → common sense stories
- **OpenHermes2.5** → diverse stories (code and advanced chemistry subsets excluded)

### 2. Large-Scale Generation (`generation/` directory)

Uses **llm-swarm** (https://github.com/huggingface/llm-swarm) — HF's scalable generation library:

```bash
cd llm-swarm
python ./examples/textbooks/generate_synthetic_textbooks.py \
  --model mistralai/Mixtral-8x7B-Instruct-v0.1 \
  --instances 2 \
  --prompts_dataset "HuggingFaceTB/cosmopedia-100k" \
  --prompt_column prompt \
  --max_samples -1 \
  --checkpoint_path "./tests_data" \
  --repo_id "HuggingFaceTB/generations_cosmopedia_100k" \
  --checkpoint_interval 500
```

**Key details:**
- Supports TGI and vLLM inference backends
- Deployed on H100 GPUs from HF Science cluster
- Total: 10,000+ GPU hours for v1
- Wandb integration for monitoring throughput and token counts
- Checkpoint-and-resume for fault tolerance

### 3. Deduplication (`deduplication/` directory)

Uses **datatrove** (https://github.com/huggingface/datatrove) for MinHash deduplication:
- MinHash signature computation across all generated documents
- LSH (Locality-Sensitive Hashing) for efficient approximate deduplication
- Near-duplicate detection and removal

### 4. Benchmark Decontamination (`decontamination/` directory)

1. **10-gram overlap detection**: identify candidate contaminated samples against all test benchmarks
2. **SequenceMatcher verification**: use `difflib.SequenceMatcher` to compare
3. **Threshold discard**: if `len(matched_substrings) / len(benchmark_sample) > 0.5`, discard

**Contamination found (v1):**
| Source | ARC | BoolQ | HellaSwag | PIQA |
|--------|-----|-------|-----------|------|
| web+stanford+openstax | 49 | 386 | 6 | 5 |
| auto_math_text+khanacademy | 17 | 34 | 1 | 0 |
| stories | 53 | 27 | 3 | 6 |

<4 contaminated for MMLU, OpenBookQA, WinoGrande.

### 5. Evaluation (`evaluation/` directory)

Uses **lighteval** (https://github.com/huggingface/lighteval):
- Standardized benchmarks for base pre-trained models
- Comparison against TinyLlama 1.1B, Qwen-1.5-1B, Phi-1.5
- Cosmo-1B outperforms TinyLlama on ARC-easy, ARC-challenge, OpenBookQA, MMLU

### 6. Educational Classification (`classification/` directory)

Added for v2: FineWeb-Edu classifier adapted to score synthetic content quality, filtering lower-quality generations.

## Cosmopedia v1 vs v2

| Aspect | v1 | v2 |
|--------|----|----|
| **Seed data** | RefinedWeb clusters | FineWeb clusters + Edu classifier |
| **Topic control** | Less controlled | More controlled (classifier-filtered) |
| **Prompt quality** | Basic audience×style matrix | Refined prompts with better seed alignment |
| **Generator tested** | Mixtral-8x7B | Also tested Llama3-70B, Mixtral-8x22B, Qwen1.5-72B (no gain) |
| **Tokens** | 25B | 28B |
| **Used in** | Cosmo-1B | SmolLM family |

## Dataset Structure

**Repository:** https://huggingface.co/datasets/HuggingFaceTB/cosmopedia

**8 subsets (configs):**
| Subset | Rows | Description |
|--------|------|-------------|
| auto_math_text | 1.95M | Math textbooks from AutoMathText seed |
| khanacademy | 24.1K | Khan Academy topic textbooks |
| openstax | 126K | OpenStax open textbooks |
| stanford | 1.02M | Stanford course textbooks |
| stories | 4.99M | Stories from UltraChat/OpenHermes seeds |
| web_samples_v1 | 12.4M | Web-sampled textbooks (v1 prompts) |
| web_samples_v2 | 10.3M | Web-sampled textbooks (v2 prompts) |
| wikihow | 179K | WikiHow how-to articles |

**Features:**
- `prompt` (string): The prompt used for generation
- `text` (string): The generated synthetic content
- `text_token_length` (int64): Token count of `text`
- `seed_data` (string): Source identifier
- `format` (string): Generation format
- `audience` (string): Target audience

## Training Stack (Cosmo-1B)

- **Architecture**: Llama2 1B (decoder-only transformer)
- **Training library**: **nanotron** — HF's distributed training framework
- **Tokenization + dedup**: datatrove
- **Evaluation**: lighteval
- **Compute**: Hugging Face Science cluster

**Results:** Cosmo-1B outperforms TinyLlama 1.1B on ARC-easy, ARC-challenge, OpenBookQA, MMLU. Comparable to Qwen-1.5-1B on ARC-challenge and OpenBookQA. Still trails Phi-1.5 (quality gap vs proprietary generation).

## SmolLM Integration

SmolLM models (135M, 360M, 1.7B) trained on **SmolLM-Corpus**, combining:
1. **Cosmopedia v2** (28B tokens) — synthetic textbooks and stories
2. **Python-Edu** (4B tokens) — educational Python from The Stack
3. **FineWeb-Edu** (220B tokens) — deduplicated educational web samples

## Getting Started

### Load the dataset
```python
from datasets import load_dataset

ds = load_dataset("HuggingFaceTB/cosmopedia", "auto_math_text", split="train")
sample = ds[0]
print(sample["prompt"][:200])
print(sample["seed_data"], sample["format"], sample["audience"])
```

### Reproduce generation
```bash
git clone https://github.com/huggingface/cosmopedia
cd cosmopedia/generation
python generate_synthetic_textbooks.py \
  --model mistralai/Mixtral-8x7B-Instruct-v0.1 \
  --instances 4 \
  --prompts_dataset "your-prompt-dataset" \
  --prompt_column prompt \
  --max_samples 100000 \
  --checkpoint_path "./checkpoints" \
  --repo_id "your-org/generations"
```

## Key Repositories

| Component | URL |
|-----------|-----|
| Cosmopedia code | https://github.com/huggingface/cosmopedia |
| Dataset (v1) | https://huggingface.co/datasets/HuggingFaceTB/cosmopedia |
| Dataset (100K sample) | https://huggingface.co/datasets/HuggingFaceTB/cosmopedia-100k |
| Cosmo-1B model | https://huggingface.co/HuggingFaceTB/cosmopedian-1b |
| llm-swarm (generation) | https://github.com/huggingface/llm-swarm |
| datatrove (dedup) | https://github.com/huggingface/datatrove |
| lighteval (evaluation) | https://github.com/huggingface/lighteval |
| nanotron (training) | https://github.com/huggingface/nanotron |
| text-clustering | https://github.com/huggingface/text-clustering |
| Blog post (v1) | https://huggingface.co/blog/cosmopedia |
| Blog post (SmolLM) | https://huggingface.co/blog/smollm |

## Pitfalls

- **Hallucination**: Mixtral can produce incorrect facts, especially in math/history. RAG-based retrieval suggested for v3.
- **Phrase repetition**: Model defaults to stock phrases ("Once upon a time"). Explicit anti-phrasing instructions needed.
- **Topic coverage**: Web clusters may not cover all desired domains. Curated sources needed for niche educational material.
- **Compute cost**: 10K+ GPU hours for 25B tokens. For smaller budgets, use the 100K sample dataset.
- **Deduplication is essential**: Without MinHash dedup, near-duplicate content inflates token counts significantly.
- **Benchmark contamination**: Always decontaminate against ALL downstream eval benchmarks before training.
- **Generator model choice**: Mixtral-8x7B performs comparably to much larger models (Llama3-70B, Qwen1.5-72B) — bigger is not always better.
- **Not a replacement for web data**: Purely synthetic training underperforms mixed training. Best results combine synthetic + curated web data.
