---
title: mergekit — Model Merging Toolkit
description: Merge pre-trained language models in weight space using mergekit: algorithms, configuration, LoRA extraction, MoE merging, evolutionary optimization, and tokenizer transplantation.
author: SakThai
---

# Hugging Face mergekit

## Overview

`mergekit` is an open-source toolkit for merging pre-trained language models by operating directly in their weight space. It uses an **out-of-core approach** (lazy tensor loading), so merges can run entirely on CPU or with as little as **~8 GB of VRAM**. Mergekit is maintained by Arcee AI and published under LGPL v3.

**Key idea:** Merging combines model strengths without ensembling overhead — a merged model retains single-model inference cost while often achieving comparable or superior performance to ensembles.

**Repository:** https://github.com/arcee-ai/mergekit

---

## Installation

```sh
git clone https://github.com/arcee-ai/mergekit.git
cd mergekit
pip install -e .
```

For extras (evolution, vLLM, etc.):

```sh
pip install -e .[evolve,vllm]
```

---

## Core Concepts

### Merge Configuration (YAML)

All merging is driven by a YAML config file. Key top-level fields:

| Field | Purpose |
|-------|---------|
| `merge_method` | Which algorithm to use (see methods below). |
| `base_model` | Base checkpoint for task-vector methods. |
| `models` | Ordered list of model sources (paths or HF Hub IDs). |
| `slices` | Layer-wise assembly (Frankenmerging); mutually exclusive with `models`. |
| `parameters` | Default merge parameters (weights, density, etc.). |
| `dtype` | Data type for the operation (e.g. `float32`, `bfloat16`). |
| `tokenizer` | Tokenizer configuration (new field). |
| `tokenizer_source` | Legacy tokenizer field (`\"union\"`, `\"base\"`, or model path). |
| `chat_template` | Chat template for the merged model (`\"auto\"`, built-in names, or Jinja2). |

### Parameter Precedence

Parameters can be set at multiple levels with decreasing precedence:

1. `slices.*.sources.parameters` → specific source slice
2. `slices.*.parameters` → specific output slice
3. `models.*.parameters` → specific model weights
4. `parameters` → global default

Values may also be **gradients** (lists) for layer-wise interpolation.

---

## Merge Methods

### Basic
- **`linear`** — Weighted average of parameters. Great for model soups and averaging similar checkpoints.
- **`passthrough`** — Directly copies tensors from one input. Foundation for Frankenmerging and layer surgery.

### Spherical Interpolation
- **`slerp`** — Spherical linear interpolation between exactly 2 models (1 base required).
- **`nuslerp`** — Enhanced SLERP; supports task-vector SLERP when a `base_model` is provided.
- **`multislerp`** — Barycentric spherical interpolation for ≥2 models.
- **`karcher`** — Riemannian barycenter (geometrically sound manifold averaging). No base model.

### Task Vector Methods (require a `base_model`)
These methods operate on *task vectors* (fine-tune deltas from a common ancestor), which reduces interference when combining specialized models.

- **`task_arithmetic`** — Combine task vectors and add back to base. Reference for controlled skill transfer.
- **`ties`** — Task Arithmetic + sparsification + sign consensus. Good for merging many models.
- **`dare_linear`** — DARE pruning without TIES sign consensus.
- **`dare_ties`** — DARE pruning *with* TIES sign consensus. Often outperforms vanilla TIES.
- **`della`** — Adaptive magnitude-based pruning + TIES sign consensus.
- **`della_linear`** — Same pruning, without TIES sign consensus.
- **`breadcrumbs`** — Remove both largest and smallest magnitudes, keeping mid-range changes.
- **`breadcrumbs_ties`** — Breadcrumbs + TIES sign consensus.
- **`sce`** — Adaptive matrix-level weighting based on variance, then sign consensus.

### Specialized
- **`model_stock`** — Geometric weight from pairwise cosine similarities of task vectors. Requires ≥3 models (1 base + ≥2 others).
- **`nearswap`** — Interpolate parameters selectively where base and secondary are similar.
- **`arcee_fusion`** — Dynamic thresholding and KL-divergence-based fusion mask between base and secondary.
- **`ram` / `ramplus_tl`** — Reinforced Agent Merging for RL-trained agents; classifies parameters as inactive/unique/shared.

### Quick-Method Cheat Sheet

| Method | Models | Base Required? | Best For |
|--------|--------|---------------|---------|
| `linear` | ≥2 | No | Model soups, similar checkpoints |
| `slerp` | 2 | Yes | Smooth transition between two models |
| `nuslerp` | 2 | Optional | Flexible SLERP / task-vector interpolation |
| `multislerp` | ≥2 | Optional | Spherical average of many models |
| `karcher` | ≥2 | No | Robust manifold averaging |
| `task_arithmetic` | ≥2 | Yes | Combining fine-tuned skills |
| `ties` | ≥2 | Yes | Multi-model merging with less interference |
| `dare_ties` | ≥2 | Yes | Robust multi-model merging |
| `della` | ≥2 | Yes | Magnitude-aware pruning + sign consensus |
| `breadcrumbs` | ≥2 | Yes | Removing noisy extreme changes |
| `sce` | ≥2 | Yes | Matrix-level adaptive weighting |
| `model_stock` | ≥3 | Yes | Principled linear weight optimization |
| `nearswap` | 2 | Yes | Preserving base where models differ |
| `arcee_fusion` | 2 | Yes | Salience-driven fusion |
| `passthrough` | 1 | No | Frankenmerging / layer splicing |

---

## CLI Entry Points

| Command | Purpose |
|---------|---------|
| `mergekit-yaml` | Main merge from a YAML config. Flags: `--cuda`, `--lazy-unpickle`, `--allow-crimes`. |
| `mergekit-extract-lora` | Extract PEFT-compatible LoRA weights from a fine-tuned checkpoint vs. base. |
| `mergekit-moe` | Merge dense models into a Mixture of Experts checkpoint. |
| `mergekit-multi` | Multi-stage merging pipeline (YAML defines dependent merge stages). |
| `mergekit-pytorch` | Merge arbitrary PyTorch / safetensors checkpoints (not necessarily HF Transformers). |
| `mergekit-tokensurgeon` | Transplant / align tokenizers between models (useful for draft models / speculative decoding). |
| `mergekit-evolve` | Evolutionary optimization (CMA-ES) of merge parameters against lm-eval harness tasks. |

---

## Tokenizer Configuration

Modern config uses the `tokenizer` block:

```yaml
tokenizer:
  source: "union"       # or "base" or a specific model path
  pad_to_multiple_of: null
  tokens:
    special_token_name:
      source: "model_path_or_kind"
      force: true        # optional: force this embedding for all models
```

**Embedding fallback rules** (for tokens missing in some models):
1. If base model has the token, use base embedding.
2. If only one model has the token, use that model's embedding.
3. Otherwise, average all available embeddings.

The merge method then decides how per-model embeddings are *combined* (SLERP, linear, etc.).

---

## Examples

### Simple Linear Merge

```yaml
merge_method: linear
parameters:
  weight: [0.5, 0.5]
models:
  - model: org/model-A
  - model: org/model-B
dtype: bfloat16
```

### Task Arithmetic Merge

```yaml
merge_method: task_arithmetic
base_model: org/base-model
parameters:
  weight: [0.6, 0.4]
  lambda: 1.0
models:
  - model: org/finetune-coding
  - model: org/finetune-instruction
```

### SLERP Between Two Models

```yaml
merge_method: slerp
base_model: org/base-model
parameters:
  t: 0.5
models:
  - model: org/model-alpha
  - model: org/model-beta
```

### Frankenmerging (Layer Slicing)

```yaml
merge_method: passthrough
slices:
  - sources:
      - model: org/model-A
        layer_range: [0, 12]
      - model: org/model-B
        layer_range: [12, 32]
dtype: float32
```

---

## Uploading to Hugging Face Hub

After a successful merge, upload with `huggingface-cli`:

```sh
huggingface-cli login
huggingface-cli upload your-username/my-merged-model ./output-model-directory .
```

`mergekit` generates a `README.md` model card automatically; edit it before uploading.

---

## Evolutionary Optimization (`mergekit-evolve`)

`mergekit-evolve` uses **CMA-ES** to search over merge parameters and optimizes them against tasks defined in the **EleutherAI LM Evaluation Harness**.

Genome YAML example:

```yaml
genome:
  models:
    - org/model-A
    - org/model-B
  merge_method: dare_ties
  base_model: org/base
  layer_granularity: 8   # parameter block size
  normalize: false
  allow_negative_weights: true
  smooth: false
  filters: [self_attn, mlp]

tasks:
  - name: hellaswag
    weight: 1.0
    metric: "acc,none"
```

- Supports single-node and multi-node (Ray cluster) execution.
- Can install with `pip install -e .[evolve,vllm]`. If flash attention conflicts, reinstall `flash-attn` after vLLM.

---

## Key Facts & Pitfalls

- **VRAM is not a blocker** — `--lazy-unpickle` + CPU execution can merge large models on modest hardware.
- **`base_model` semantics matter** — task-vector methods require a real shared ancestor; otherwise deltas are meaningless.
- **`--allow-crimes`** — mergekit warns when models with incompatible architectures are merged; this flag disables the check. Use with caution.
- **Tokenizer `union` mode** combines vocabularies, which can create large embedding matrices — monitor output model size.
- **Layer granularity** in evolution trades off speed vs. solution quality; fine-grained is slower but may find better recipes.
- **MoE merging** (`mergekit-moe`) produces dense-to-expert conversions, not always a drop-in replacement for dense models.

---

## References

- Paper: https://aclanthology.org/2024.emnlp-industry.36/
- GitHub: https://github.com/arcee-ai/mergekit
- Merge Method Docs: https://github.com/arcee-ai/mergekit/blob/main/docs/merge_methods.md
- Evolutionary Merge Docs: https://github.com/arcee-ai/mergekit/blob/main/docs/evolve.md
- Frankenmerging Docs: https://github.com/arcee-ai/mergekit/blob/main/docs/multimerge.md
- MoE Docs: https://github.com/arcee-ai/mergekit/blob/main/docs/moe.md
