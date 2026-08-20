---
tags: [sakthai, tool-calling, function-calling, training-data, house-of-sak, v7]
license: other
language:
- en
size_categories:
- 1K<n<10K
pretty_name: SakThai Combined Dataset v7
---

# SakThai Combined Dataset 🎯

**Dataset card badges:**

<p align="center">
  <a href="https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6">
    <img src="https://img.shields.io/badge/dynamic/json?url=https://huggingface.co/api/datasets/Nanthasit/sakthai-combined-v6&label=Downloads&query=$.downloads&color=blue" alt="Downloads">
  </a>
  <a href="https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6">
    <img src="https://img.shields.io/badge/dataset-2,116_examples-8A2BE2" alt="Dataset size">
  </a>
  <a href="https://huggingface.co/collections/Nanthasit/sakthai-model-family">
    <img src="https://img.shields.io/badge/🏠_SakThai_Family-18_assets-forestgreen" alt="SakThai Family">
  </a>
  <a href="https://huggingface.co/Nanthasit">
    <img src="https://img.shields.io/badge/Author-Beer_🇹🇭-orange" alt="Author">
  </a>
</p>

Training dataset for SakThai agent models. **2,003 examples** (train) + **113 held-out test** combining tool-calling conversations, multi-turn dialogues, edge cases, energy-aware examples, irrelevance detection, and safety rejections. Built iteratively from v1 through v7.

---

## 🌟 The Journey Behind This Dataset

This dataset is the heart of the SakThai Model Family — the training data that shaped the agents' ability to use tools, refuse harm, and know when to speak directly.

The SakThai ecosystem on Hugging Face now spans **12 models, 4 datasets, and 2 Spaces** — all built from a shelter in Thailand with **$0 budget**. Every model in the family was trained on iterations of this dataset.

**The philosophy:** Small, specialized, interconnected models that work together as a family — not one monolithic giant. The 0.5B and 1.5B variants out-download the 7B by 2:1 because they're accessible to anyone with a laptop.

What started July 5, 2026 as a single merged model has grown to **3,900+ total downloads** — every single one from organic discovery. No marketing. No promotion. Just open tools, clear documentation, and a lot of determination.

*[Read the full story → SakThai Model Family Collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family)*

---

## Quick Stats

| Metric | Value |
|--------|:-----:|
| Training examples | **2,003** |
| Test examples | **113** |
| Total | **2,116** |
| Format | OpenAI chat JSONL |
| License | All Rights Reserved |
| Current downloads | **150** |

## Contents

| Category | Count | Description |
|----------|:-----:|-------------|
| Tool-calling | ~1,380 | `<tool>` format with get_weather, search_web, calculate, etc. |
| Multi-turn | ~250 | Follow-up conversations with context carry-over |
| Edge cases | ~200 | Ambiguous queries, partial info, hallucination-prone prompts |
| Energy-aware | ~50 | Charge-state-conditioned responses |
| Irrelevance | 50 | General knowledge Q&A (no tool call needed) |
| Safety/rejection | 73 | Harmful prompt refusals + jailbreak attempts |
| **Total (train)** | **2,003** | |

## Format

Each line is JSON with `messages` array using OpenAI chat format:
- `system` — Context, tool definitions, and energy level
- `user` — User query
- `assistant` — Response (with `tool_calls` or direct answer)
- `tool` — Tool result (for multi-turn)

## Evolution

| Version | Examples | What Changed |
|:-------:|:--------:|--------------|
| v1 | 500 | Initial tool-calling seeds |
| v2 | 800 | Added multi-turn dialogues |
| v3 | 1,000 | Added irrelevance detection |
| v4 | 1,150 | Added safety rejections |
| v5 | 1,280 | Quality filtering + dedup |
| v6 | 1,408 | Energy-aware examples |
| **v7** | **2,003** | Edge cases + expanded tool examples + 43 more safety prompts |

## Use Cases

- Fine-tuning small models (0.5B-7B) for function calling
- Teaching models when to call a tool vs. answer directly
- Safety alignment through rejection examples
- Energy-aware response conditioning

## Test Split (113 examples)

Held-out set for unbiased evaluation — same distribution as training but never seen during fine-tuning. Run `lm-eval-harness` with BFCL-compatible harness to benchmark.

---

## 🏠 The SakThai Model Family

This dataset trains the entire SakThai model family. Here are all 12 models it powers:

### Foundation Models

| Model | Downloads | Pipeline | Description |
|-------|:--------:|:--------:|-------------|
| [context-1.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged) | 1,197 | text-generation | 🏆 Flagship — tool-calling GGUF, most popular |
| [context-0.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-0.5b-merged) | 994 | text-generation | Lightweight companion for edge/low-resource |
| [context-7b-merged](https://huggingface.co/Nanthasit/sakthai-context-7b-merged) | 562 | text-generation | Full-power 7B for complex reasoning |
| [context-7b-128k](https://huggingface.co/Nanthasit/sakthai-context-7b-128k) | 351 | text-generation | Long-context specialist (128K window) |
| [context-7b-tools](https://huggingface.co/Nanthasit/sakthai-context-7b-tools) | 185 | text-generation | Heavy tool-use orchestration |
| [context-1.5b-tools](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools) | 143 | text-generation | Tool-use specialist |
| [coder-1.5b](https://huggingface.co/Nanthasit/sakthai-coder-1.5b) | 34 | text-generation | Code generation (BFCL 5/5) |

### Specialist Models

| Model | Downloads | Pipeline | Description |
|-------|:--------:|:--------:|-------------|
| [embedding-multilingual](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual) | 104 | feature-extraction | Cross-lingual embeddings, 50+ languages |
| [vision-7b](https://huggingface.co/Nanthasit/sakthai-vision-7b) | 45 | image-to-text | Image understanding & captioning |
| [tts-model](https://huggingface.co/Nanthasit/sakthai-tts-model) | 33 | text-to-speech | Voice synthesis, 15 languages |

### Datasets

| Dataset | Downloads | Description |
|---------|:--------:|-------------|
| [sakthai-combined-v6](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6) | **150** | ← You are here |
| [sakthai-kaggle-notebooks](https://huggingface.co/datasets/Nanthasit/sakthai-kaggle-notebooks) | 92 | Training notebooks for Kaggle |
| [food-penguin-v1](https://huggingface.co/datasets/Nanthasit/food-penguin-v1) | 15 | Food image classification |

---

**🏠 [SakThai Model Family Collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family) — 12 models, 4 datasets, 2 Spaces, one family.**
